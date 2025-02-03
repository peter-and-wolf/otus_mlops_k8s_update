# otus_mlops_k8s_update

## FastAPI-приложение

[back/train.ipynb](back/train.ipynb) – терадка с кодом, который учит две простые модели классификации: Linear Regression и Tree Classifier. 

[back/app](back/app) – FastApi-приложение, оборачивающее модель классификации в REST-интерфейс. Ручки такие:

* `GET api/v1/version` – возвращает версию приложения и название модели, c которой оно работает;
* `POST api/v1/predict` – принимат текст, исполняет модель и возвращает score;
* `GET api/v1/startup`, `GET api/v1/ready`, `GET api/v1/health` – ручки, возвращающее состояние приложения ([probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/));

Запустить приложение можно так:

```bash
cd back/app
ML_MODEL_PATH=../models/lr.pkl uvicorn main:app --host 0.0.0.0 --port 8888
```

## Докеризация приложения

[back/Dockerfile] – [Dockerfile](https://docs.docker.com/reference/dockerfile/), с помощью которого можно собрать образ с приложением и моделью внутри. Образ параметризирован, с помощью параметра `MODEL_TO_USE` можно управлять тем, какая модель окажется внутри.

Так можно собрать образ с линейной регрессией:

```bash
docker build --build-arg MODEL_TO_USE=lr.pkl -t peterwolf/jokemeter:lr .
```

А вот так – с решающим деревом:

```bash
docker build --build-arg MODEL_TO_USE=tr.pkl -t peterwolf/jokemeter:tr .
```

Запустить приложение из собранного образа можно так:

```bash
docker run -p 8000:80 peterwolf/jokemeter:lr
```

или так:

```bash
docker run -p 8000:80 peterwolf/jokemeter:tr
```

Проверить, что все работает, можно так:

```bash
curl localhost:8000/api/v1/version
```

или так:

```bash
curl -H "Content-Type: application/json" --data '{"text": "Ходит дурачок по лесу, ищет дурачок глупее себя", "joker": "None"}' localhost:8000/api/v1/predict
```

Так как мы собираемся деплоить приложения, основанные на этих образах, в k8s, нужно, чтобы кубер мог эти образы откуда-то скачать. Проще всего загрузить их в [Docker Hub](https://hub.docker.com/). Я буду загружать в свой аккаунт, а вы лучше загружайте в свой :)

```bash
# Логинимся в Docker Hub
docker login

# Загружаем оба образа
docker push peterwolf/jokemeter:lr
docker push peterwolf/jokemeter:tr
```

## Деплой приложения в k8s

[k8s/jokemeter-deployment.yaml](k8s/jokemeter-deployment.yaml) – манифест, с помощью которого можно развернуть наше приложение в k8s так:

```bash
kubectl apply -f jokemeter-deployment.yaml
```

Проверить, что все запустилось, можно, вытащив нуружу TCP-порт: 

```bash
kubectl port-forward deployments/jokemeter-deployment 8000:80

# Звоним курлом на 127.0.0.1:8000, трафик попадает в контейнер пода
curl localhost:8000/api/v1/version
```

## Направляем трафик в кластер (Ingress)

> Все манифесты находтся в папке [k8s](k8s).

Пробрасывать порты – это способ отладки, который: 

* недолговечен (прибили команду, и все);
* требует доступа к API кластера; 

Продуктовая история – запускать HTTP-трафик в клачтер через [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/).

Ingress – это компонент, который дотягивает HTTP/HTPS трафик до [служб](https://kubernetes.io/docs/concepts/services-networking/service/) k8s, которые распределяют трафик между подами. Это значит, что нужно создать службу. В нашем случае подойдет [ClusterIP](https://kubernetes.io/docs/concepts/services-networking/service/#type-clusterip). 

```bash
kubectl apply -f jokemeter-service.yaml
```

Теперь необходимо установить Ingress-контроллер, который будет управлять [Ingress-ресурсами](https://kubernetes.io/docs/concepts/services-networking/ingress/#the-ingress-resource).

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Ждем, пока все очухается
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

И создать [Ingress-ресурсами](https://kubernetes.io/docs/concepts/services-networking/ingress/#the-ingress-resource), который потащит трафик в поды нашего FastAPI-приложения. Активируем манифест:

```bash
kubectl apply -f jokemeter-ingress.yaml
```

Контроллер Ingress управляет своими ресурсами, которые описывают правила [L7](https://ru.wikipedia.org/wiki/%D0%9F%D1%80%D0%BE%D1%82%D0%BE%D0%BA%D0%BE%D0%BB%D1%8B_%D0%BF%D1%80%D0%B8%D0%BA%D0%BB%D0%B0%D0%B4%D0%BD%D0%BE%D0%B3%D0%BE_%D1%83%D1%80%D0%BE%D0%B2%D0%BD%D1%8F)-маршрутизации трафика: путь трафика определяется доменным именем и путем. [Манифест](k8s/jokemeter-ingress.yaml) нашего Ingress-ресурса определяет доменное имя `jokemeter.ai`. Наш kind-кластер – группа контейнеров, запущенная локально, поэтому имя `jokemeter.ai` должно превращаться в адрес `127.0.0.1`. Самый простой способ сделать это – добавить (могут потребоваться права суперпользователя) в `/etc/hosts` строчку:

```
127.0.0.1       jokemeter.ai
```

Теперь можно делать так:

```bash
curl http://jokemeter.ai/api/v1/version
```

и трафик попадет в под внутри кластера. 

## Шатаем деплой

Вот так можно посмотреть историю обновлений:

```bash
kubectl rollout history deployment/jokemeter-deployment
```

Ревизия будет всего одна, потому что мы еще ничего не обновляли. Давайте обновим, заменим образ контейнера внутри пода:

```bash
kubectl set image deployment/jokemeter-deployment jokemeter=peterwolf/jokemeter:tr
```

Ждем и наблюдаем, как произойдет обновление: стартует новый под, старый продолжает работать, пока новый окончательно не запустится. Это называется ["скользящее обновление"](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/).

Смотрим историю обновлений, теперь ревизии две:

```bash
kubectl rollout history deployment/jokemeter-deployment
```

Обновляем снова, но на этот раз намеренно указываем неправильный образ, чтобы под не мог запуститься: 

```bash
kubectl set image deployment/jokemeter-deployment jokemeter=peterwolf/jokemeter:fake
```

Смотрим историю обновлений:

```bash
kubectl rollout history deployment/jokemeter-deployment
```

Откатить обновление можно так:

```bash
kubectl rollout undo deployment/jokemeter-deployment
```

Вот так можно прыгнуть на конкретную ревизию:

```bash
kubectl rollout undo deployment/jokemeter-deployment --to-revision=<номер ревизии>
```

В номерах ревизий очень легко запутаться, но им можно давать [аннотации](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#checking-rollout-history-of-a-deployment).

Давайте еще раз модифицируем внедрение, изменим число подов. Команда такая:

```bash
kubectl scale deployment/jokemeter-deployment --replicas=3
```

И сделаем аннотацию ждя текущеей ревизии:

```bash
kubectl annotate deployment/jokemeter-deployment kubernetes.io/change-cause="the number of replicas has been increased to three" --overwrite=true
```

Проверяем историю изменений:

```bash
kubectl rollout history deployment/jokemeter-deployment
```

Видно, что с аннотациями ориентироваться легче.

Давайте снова заменим образ и понаблюдаем за поведением кубера:

```bash
kubectl set image deployment/jokemeter-deployment jokemeter=peterwolf/jokemeter:lr
```

Так работает [rollout](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)-обновление: Deployment-контроллер запускает новые поды (не более, чем [maxSurge](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#max-surge)) и гасит старые (не более, чем [maxUnavailable](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#max-unavailable)).

Теперь давайте приберем за собой, удаляем все в обратном порядке:

* Ingress-ресурс `jokemeter-ingress`;
* Службу `jokemeter-svc`;
* Внедрение `jokemeter-deployment`

Итого, чтобы установить простое приложение, нам потребовалось три шага. Чтобы удалить – еще три. Хорошая новость: есть инструмент автоматизации.

## Helm

[Helm](https://helm.sh/) – это пакетный менеджер для k8s. [Установите](https://helm.sh/docs/intro/install/) его к себе на компьютер, если еще не. 

[Вот тут](https://github.com/peter-and-wolf/otus_mlops_k8s_jokemeter) – helm-чарт (пакет) для нашего FastAPI-приложения. Склонируйте репозиторий.

Теперь в директории с репозиторием выполните команду:

```bash
helm template jokemeter .
```

Helm заполнит все плейсхолдеры `{{}}`, подготовит манифесты кубера и вывалит их на экран. 

А вот так, одной командой можно установить приложение в кластер:

```bash
helm install jokemeter .
```

Дергаем курлом:

```bash
curl http://jokemeter.ai/api/v1/version
```

Вот так, снова в одну команду все можно удалить:

```bash
helm uninstall jokemeter
```

Вернем приложение в кластер:

```bash
helm install jokemeter .
```

Очень удобно.

## ArgoCD

Рассмотрим еще один способ деплоя в кубер – [ArgoCD](https://argoproj.github.io/cd/). Сперва ставим ArgoCD в кубер.

```bash
# Создаем для него свой неймспейс
kubectl create namespace argocd

# Активируем манифест
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

ArgoCD – это web-приложение, у него есть GUI, на который ходят браузером. Как правильно запускать HTTP/HTTPS-трафик в кластер? Через Ingress, контроллер которого (весьма кстати) у нас уже есть. Осталось активировать Ingress-ресурс, манифест которого возьмите тут [k8s/argocd-ingress.yaml](k8s/argocd-ingress.yaml):

```bash
kubectl apply -f kubectl apply -f argocd-ingress.yaml
```    

Теперь добавьте в `/etc/hosts` строку:

```bash
127.0.0.1       argocd.myk8s.io
```

Идите браузером на адрес `argocd.myk8s.io` (ругнется на сертификат, игнорируйте). Логин `admin`, а пароль выковыряте из [секретов](https://kubernetes.io/docs/concepts/configuration/secret/) k8s. Команда такая:  

```bash
kubectl get secrets argocd-initial-admin-secret --namespace argocd --template {{.data.password}} | base64 -d
```

Когда залогинитесь, жмакайте на `Create Application` и заполняйте форму примерно так:

#### General

* **Application Name**: jokemeter
* **Project Name**: default
* **Sync Policy**: manual

#### Source

* **Repository URL**: https://github.com/peter-and-wolf/otus_mlops_k8s_jokemeter
* **Revision**: HEAD
* **Path**: .

#### Destination

* **Cluster IP**: https://kubernetes.default.svc
* **Namespace**: default

#### Helm

* **Values File**: values.yaml

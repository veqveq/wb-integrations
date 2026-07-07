## Деплой
Деплой сервисов проекта организован через Jenkins Pipline. Контейнер с Jenkins кастомный и требует предварительной сборки. <br>
Все конфигурационные файлы живут на локальной машине в wb-integrations-config (пока что, есть планы сделать более инженерно)
и деплоятся отдельным локальным скриптом.<br>
**БЕЗ ЗАДЕПЛОЕННЫХ КОНФИГОВ СЕРВИСЫ РАБОТАТЬ НЕ БУДУТ!**<br><br>
**КОМАНДЫ ДЛЯ ДЕПЛОЯ**
- собрать Docker-образ Jenkins
```
cd /.deploy
docker compose build --no-cache
```
- запуск Jenkins в Docker (сборка образа обязательна)
```
cd /.deploy
docker compose up -d
```
- После старта Jenkins необходимо его сконфигурировать
    - По дефолту при сборке через `docker compose` Jenkins стартует по адресу `localhost:8080`
    - Инициализация админа Jenkins:
        - После запуска контейнера попадем на страницу `Unlock Jenkins`
        - В терминале выполнить `docker exec -it jenkins cat /var/jenkins_home/secrets/initialAdminPassword`
        - Скопировать пароль и вставить его на странице - перекинет на установку плагинов
    - Список плагинов Jenkins:
        - Folders
        - Pipeline
        - Build Name and Description Setter
        - Credentials Binding
        - SSH Agent
        - Timestamper
        - Workspace cleanup
        - Git
        - Git Parameter
        - Matrix Authorization Strategy
        - Dark Theme (optional :-))
    - Далее необходимо настроить админскую учетку
    - Залогиниться под ней (произойдет автоматически после создания админа)
    - Далее необходимо прописать приватные SSH ключи `(Settings -> Credentials)`
        - К стенду, на который будет происходить деплой
        - К GitHub (если планируется собирать проект оттуда)
    - Специфические настройки для сборки из GitHub
        - Cпособ авторизации по SSH
            - Jenkins Web UI
            - Settings
            - Security
            - Git Host Key Verification Configuration
            - Выбрать в селектбоксе Accept first connection
    - Создать Jenkins pipeline `(Web UI Start page -> Create job -> pipeline)`. Настройки
        - Удалять устаревшие сборк
        - Definition:
            - Pipeline script - сборка внутри Jenkins, скопировать содержимое файла в проекте .deploy/Jenkinsfile
            - Pipeline script from SCM - сборка из GitHub (нужно форкнуть к себе репу и создать свой SSH для подключения)
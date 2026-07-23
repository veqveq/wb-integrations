# Сервисы домашних интеграций устройств в Wirenboard

## Список сервисов
- чтение событий обнаружения движений с камер Hikvision (`camera_alarm`)
- получение клиентов локальной сети с роутера Keenetic (`network_clients_checker`)
- определение уровня освещения с камер Hikvision (`camera_light_sensor`)

## [Деплой](./.deploy/README.md)

## Информация по размещению файло
- Директория сервисов на стенде - `/mnt/data/wb-integrations`
- Директория конфигурационных файлов `/etc/wb-integrations`
- Директория размещения шаблонов устройств `/etc/wb-rules/`

## Основные команды для работы с сервисами на стенде
- получить список работающих сервисов `systemctl list-units --type=service --state=running`
- стартануть сервис `systemctl start <service>.service`
- остановить сервис `systemctl stop <service>.service`
- перезапустить сервис `systemctl restart <service>.service`
- проверить статус сервиса `systemctl status <service>.service`
- чтение логов в системном журнале `journalctl -u <service>.service`
- чтение логов в из файла сервиса
  - логи камер `nano /mnt/data/wb-integrations/hikvision/camera/logs/<cameraName>.log`
  - логи роутера `nano /mnt/data/wb-integrations/keenetic/logs/logs.log`
  - логи MQTT `nano /mnt/data/wb-integrations/mqtt/logs/logs.log`
  - логи camera_alarm `nano /mnt/data/wb-integrations/security/camera_alarm/logs/logs.log`
  - логи network_clients_checker `nano /mnt/data/wb-integrations/security/network_clients_checker/logs/logs.log`
  - логи camera_light_sensor `nano /mnt/data/wb-integrations/sensor/camera_light_sensor/logs/logs.log`


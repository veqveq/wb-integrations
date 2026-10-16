var CUSTOM_SERVICES_NAMES = [
    "camera_light_sensor",
    "camera_alarm",
    "network_clients_checker"
]

for (var index in CUSTOM_SERVICES_NAMES) {
    startService(CUSTOM_SERVICES_NAMES[index])
}

function startService(serviceName) {
    runShellCommand("systemctl restart {}.service".format(serviceName), {
        captureOutput: true,
        exitCallback: function(exitCode) {
            if (exitCode !== 0) {
                log.error("Ошибка запуска пользовательского сервиса {}: {}".format(serviceName, exitCode))
                return
            }
            log("Сервис {} запущен".format(serviceName));
        }
    })
}

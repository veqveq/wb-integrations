// ================================
// ========== Констранты ==========
// ================================
// Структура файла конфигурации
// {
//   "clientId": <Произвольное название клиента для http-запросов>,
//   "auth": <логин:пароль от аккаунта lk.zont.online (Обязательно в Base64 кодировке)>,
//   "zontDeviceTopic": <Название топика MQTT, в который пишет ZONT (как в настройках ZONT, без названия конкретного устройства)>,
//   "zontControlsTopic": <Название топика MQTT, из которого читает ZONT (как в настройках ZONT, без названия конкретного устройства)>
// }
var CONFIG = readConfig("/etc/zont-config.conf");

var AUTH_CURL = "curl --location --request POST 'https://my.zont.online/api/get_authtoken' \
--header 'X-ZONT-Client: {}' \
--header 'Content-Type: application/json' \
--header 'Authorization: Basic {}'";

var DEVICES_CURL = "curl --location --request POST 'my.zont.online/api/devices' \
--header 'Content-Type: application/json' \
--header 'X-ZONT-Client: {}' \
--header 'X-ZONT-Token: {}'";

var DEVICE_TEMPLATES = {
    "temperatureSensor": {
        "zontDeviceNames": ["wired_temperature_sensors", "analog_temperature_sensors"],
        "titlePrefix": "[Датчик]",
        "virtualDeviceMeta": {
            "t": {
                "controlName": "sensorValue",
                "name": "Температура",
                "type": "temperature",
                "value": "0",
                "readonly": true,
            },
            "a": {
                "controlName": "status",
                "name": "Доступность",
                "type": "switch",
                "value": false,
                "readonly": true
            }
        }
    },
    "pressureSensor": {
        "zontDeviceNames": ["analog_inputs"],
        "titlePrefix": "[Датчик]",
        "virtualDeviceMeta": {
            "v": {
                "controlName": "sensorValue",
                "name": "Давление",
                "type": "pressure",
                "readonly": true
            },
            "a": {
                "controlName": "status",
                "name": "Доступность",
                "type": "switch",
                "value": false,
                "readonly": true
            }
        }
    },
    "relay": {
        "zontDeviceNames": ["relay_controls"],
        "titlePrefix": "[Реле]",
        "virtualDeviceMeta": {
            "s": {
                "controlName": "state",
                "name": "Состояние",
                "type": "switch",
                "value": false,
                "readonly": false
            }
        }
    },
    "pump": {
        "zontDeviceNames": ["pumps"],
        "titlePrefix": "[Насос]",
        "virtualDeviceMeta": {
            "s": {
                "controlName": "state",
                "name": "Состояние",
                "type": "switch",
                "value": false,
                "readonly": false
            }
        }
    },
    "heatingCircuit": {
        "zontDeviceNames": ["heating_circuits"],
        "criteriasForExclude": {
            "type": 0
        },
        "titlePrefix": "[Контур]",
        "virtualDeviceMeta": {
            "s": {
                "controlName": "targertTemperature",
                "name": "Целевая температура",
                "type": "range",
                "min": "water_min_temperature",
                "max": "water_max_temperature",
                "value": 0,
                "readonly": false
            },
            "c": {
                "controlName": "currentTemperature",
                "name": "Текущая температура",
                "type": "temperature",
                "precision": 1,
                "readonly": true
            }
        }
    },
    "boiler": {
        "zontDeviceNames": ["boiler_adapters"],
        "titlePrefix": "[Котел]",
        "virtualDeviceMeta": {
            "water": {
                "controlName": "currentTemperature",
                "name": "Температура теплоносителя",
                "type": "temperature",
                "precision": 0.1,
                "value": 0,
                "readonly": true,
                "order": 1
            },
            "state": {
                "controlName": "state",
                "name": "Состояние",
                "type": "value",
                "value": 0,
                "enumValues": {
                    "0": {
                        "ru": "Выключен"
                    },
                    "1": {
                        "ru": "Работает"
                    },
                    "2": {
                        "ru": "Ошибка"
                    }
                },
                "readonly": true,
                "order": 0
            },
            "modul": {
                "controlName": "modulLevel",
                "name": "Уровень модуляции",
                "type": "range",
                "min": 0,
                "max": 100,
                "value": 0,
                "readonly": true,
                "order": 2
            },
            "err": {
                "controlName": "errorText",
                "name": "Текст ошибки",
                "type": "value",
                "value": "",
                "readonly": true,
                "order": 3
            },
        }
    },
    "mixingValve": {
        "zontDeviceNames": ["threeway_taps"],
        "titlePrefix": "[Трехходовой клапан]",
        "virtualDeviceMeta": {
            "s": {
                "controlName": "status",
                "name": "Состояние",
                "type": "value",
                "value": 0,
                "enumValues": {
                    "0": {
                        "ru": "Не активен"
                    },
                    "1": {
                        "ru": "Открывается"
                    },
                    "2": {
                        "ru": "Закрывается"
                    }
                },
                "readonly": true,
                "order": 0
            },
            "state": {
                "controlName": "state",
                "name": "Открыт",
                "type": "switch",
                "value": false,
                "readonly": false,
                "zontCommandsByWbControlValue": {
                    "true": "1",
                    "false": "2"
                },
                "order": 1
            },
            "openByStep": {
                "controlName": "openByStep",
                "name": "Открыть на шаг",
                "type": "pushbutton",
                "value": 1,
                "readonly": false,
                "zontCommandsByWbControlValue": {
                    "true": "3"
                },
                "order": 2
            },
            "closeByStep": {
                "controlName": "closeByStep",
                "name": "Закрыть на шаг",
                "type": "pushbutton",
                "value": 1,
                "readonly": false,
                "zontCommandsByWbControlValue": {
                    "true": "4"
                },
                "order": 3
            }
        }
    }
}

// ==================================
// ========== HTTP-запросы ==========
// ==================================

runShellCommand(AUTH_CURL.format(CONFIG["clientId"], CONFIG["auth"]), {
    captureOutput: true,
    exitCallback: function(exitCode, output) {
        output = JSON.parse(output)
        if (!output["ok"] || output["token"] == null || output["token"] == undefined) {
            log.error("Ошибка авторизации: " + output["error_ui"])
            return null
        }
        log("Авторизация на zont.online выполнена");
        token=output["token"]
        getDevicesMeta(token)
    }
})

function getDevicesMeta(token) {
    runShellCommand(DEVICES_CURL.format(CONFIG["clientId"], token), {
        captureOutput: true,
        exitCallback: function(exitCode, output) {
            output = JSON.parse(output)
            if (!output["ok"]) {
                log.error("Ошибка получения списка устройств: " + output["error_ui"])
                return
            }
            log("Список устройств получен");
            for (var index = 0; index < output.devices.length; index++) {
                var device = output.devices[index]
                createVirtualDevices(device.z3k_config)
            }

        }
    });
}

// ==================================
// ========== MQTT-запросы ==========
// ==================================

function subscribeToZontTopic(zontDeviceName, virtualDeviceName, virtualDeviceParams) {
    trackMqtt(CONFIG["zontDeviceTopic"] + zontDeviceName, function(msg) {
        var virtualDevice = dev[virtualDeviceName]
        for (var zontParamName in virtualDeviceParams) {
            var param = virtualDeviceParams[zontParamName]
            var virtualDeviceParam = param.controlName
            var topicData = JSON.parse(msg["value"]);
            if (zontParamName in topicData) {
                var value = topicData[zontParamName]
                if (param.type === "switch") {
                    value = value === 1
                }
                virtualDevice[virtualDeviceParam] = value
            }
        }
    });
}

function createTopicProducers(zontDeviceId, virtualDeviceName, virtualDeviceParams) {
    for (var zontParamName in virtualDeviceParams) {
        var param = virtualDeviceParams[zontParamName]
        if (!param.readonly) {
            (function (param) {
                defineRule("{}-{}".format(virtualDeviceName, zontParamName), {
                    whenChanged: "{}/{}".format(virtualDeviceName, param.controlName),
                    then: function(value) {
                        var command = String(prepareCommand(param, value))
                        if (command == null) {
                            return
                        }
                        var message = {
                            "Id": zontDeviceId,
                            "cmd": command
                        }
                        message = JSON.stringify(message)
                        var topic = CONFIG["zontControlsTopic"]

                        runShellCommand("mosquitto_pub -t '{}' -m '{}'".format(topic, message))
                    }
                });
            })(param)
        }
    }
}

function prepareCommand(param, value) {
    var command
    if (param.type === "switch") {
        command = value ? "1" : "0"
    }

    if (param.type === "range") {
        command = (value + 273) * 10
    }
    if ("zontCommandsByWbControlValue" in param) {
        var command = param.zontCommandsByWbControlValue[String(value)]
        if (value != null && value != "undefined" && value != "") {
            command = value
        } else {
            log.error("Неизвестная команда от устройства: {}".format(value))
            return null
        }
    }
    return command
}

// ========================================
// ========== Создание устройств ==========
// ========================================

function createVirtualDevices(devicesInfo) {
    for (var templateName in DEVICE_TEMPLATES) {
        var deviceNumber = 0
        var template = DEVICE_TEMPLATES[templateName]
        var zontDevices = []
        for (var zontDeviceName in devicesInfo) {
            if (templateApplicable(zontDeviceName, template)) {
                var deviceInfo = devicesInfo[zontDeviceName]
                for (var index = 0; index < deviceInfo.length; index++) {
                    var zontDevice = deviceInfo[index]
                    if (!excludeByCriterias(zontDevice, template) && includeByCriterias(zontDevice, template)) {
                        deviceNumber++;
                        var createdDeviceName = createVirtualDevice(zontDevice, templateName, deviceNumber)
                        log("Создано виртуальное устройство: {}".format(createdDeviceName));
                    }
                }
            }
        }
    }
}

function createVirtualDevice(zontDeviceDefinition, templateName, index) {
    var deviceName = "zont_{}_{}".format(templateName, index)
    var template = DEVICE_TEMPLATES[templateName]
    if (template.criteriasForExclude != null) {
        var criterasForExclude = template.criteriasForExclude
    }
    var virtualDeviceTitle = zontDeviceDefinition.name
    if (template.titlePrefix != null) {
        virtualDeviceTitle = "{} {}".format(template.titlePrefix, virtualDeviceTitle)
    }
    var cells = prepareVirtualDeviceCells(zontDeviceDefinition, template)

    defineVirtualDevice(deviceName, {
        title: "ZONT {}".format(virtualDeviceTitle),
        cells: cells
    });
    subscribeToZontTopic(zontDeviceDefinition.name, deviceName, template.virtualDeviceMeta)
    createTopicProducers(zontDeviceDefinition.id, deviceName, template.virtualDeviceMeta)
    return deviceName
}

function prepareVirtualDeviceCells(zontDeviceDefinition, template) {
    var cells = {}

    for (var zontParamName in template.virtualDeviceMeta) {
        var param = template.virtualDeviceMeta[zontParamName]
        var cellName = param.controlName
        var min = param.min in zontDeviceDefinition ? zontDeviceDefinition[param.min] : param.min
        var max = param.max in zontDeviceDefinition ? zontDeviceDefinition[param.max] : param.max

        cells[cellName] = {
            "title": param.name,
            "type": param.type,
            "value": param.value,
            "readonly": param.readonly
        }
        setOptionalValue(cells[cellName], "enum", param.enumValues)
        setOptionalValue(cells[cellName], "units", param.units)
        setOptionalValue(cells[cellName], "precision", param.precision)
        setOptionalValue(cells[cellName], "order", param.order)
        setOptionalValue(cells[cellName], "min", min)
        setOptionalValue(cells[cellName], "max", max)
    }
    return cells
}

// =============================
// ========== Утилиты ==========
// =============================

function setOptionalValue(json, field, value) {
    if (value != null && value !== "undefined" && value !== "") {
        json[field] = value
    }
}

function templateApplicable(zontDeviceName, template) {
    return template.zontDeviceNames.indexOf(zontDeviceName) !== -1
}

function excludeByCriterias(zontDevice, template) {
    var criterais = template.criteriasForExclude
    if (criterais) {
        for (var criteriaFieldName in criterais) {
            var criteriaFieldValue = criterais[criteriaFieldName]
            if (zontDevice[criteriaFieldName] != criteriaFieldValue) {
                return false
            }
        }
        return true
    }
    return false
}

function includeByCriterias(zontDevice, template) {
    var criterais = template.criteriasForInclude
    if (criterais) {
        for (var criteriaFieldName in criterais) {
            var criteriaFieldValue = criterais[criteriaFieldName]
            if (zontDevice[criteriaFieldName] != criteriaFieldValue) {
                return false
            }
        }
    }
    return true
}

var ROUTER = "networkClients";
var SECURITY = "securitySystem";

var trustedClients = [];
var wasTrustedPresent = false;

var autoEvent = {
    armed: false,
    client: "",
    time: ""
};

defineVirtualDevice(SECURITY, {
    title: "Система охраны",
    cells: {
        manualArm: {
            type: "switch",
            value: false,
            title: "Ручная постановка на охрану",
            order: 1
        },
        armed: {
            type: "switch",
            value: false,
            title: "Состояние охраны",
            order: 2
        },
        armClient: {
            type: "text",
            value: "",
            readonly: true,
            title: "Поставивший в охрану",
            order: 3
        },
        disarmClient: {
            type: "text",
            value: "",
            readonly: true,
            title: "Снявший с с охраны",
            order: 4
        },
        armTime: {
            type: "text",
            value: "",
            readonly: true,
            title: "Время изменения состояния",
            order: 5
        }
    }
});

defineRule("security_manual_mode", {
    whenChanged: SECURITY + "/manualArm",
    then: function(value) {
        runShellCommand("mosquitto_pub -r -t '/devices/" + SECURITY + "/controls/armed/meta/readonly' -m " + (value ? "0" : "1"))
        if (!value) {
            processTrusted();
            dev[SECURITY].armTime = autoEvent["time"];
            dev[SECURITY].armClient = "";
            dev[SECURITY].disarmClient = "";

            if (dev[SECURITY].armed) {
                dev[SECURITY].armClient = autoEvent["client"];
            } else {
                dev[SECURITY].disarmClient = autoEvent["client"];
            }
        }
    }
});

defineRule("security_manual_arm", {
    whenChanged: SECURITY + "/armed",
    then: function(value) {

        if (!dev[SECURITY].manualArm)
            return;

        dev[SECURITY].armTime = now();

        if (value) {
            dev[SECURITY].armClient = "Вручную";
            dev[SECURITY].disarmClient = "";
        } else {
            dev[SECURITY].disarmClient = "Вручную";
            dev[SECURITY].armClient = "";
        }
    }
});

defineRule("router_trusted_changed", {
    whenChanged: ROUTER + "/trustedClientsOnline",
    then: function(value) {
        if (dev[SECURITY].manualArm)
            return;

        processTrusted();
    }
});

function processTrusted()
{
    var truestedOnline = dev.networkClients.trustedClientsOnline;
    log("dev: " + dev.networkClients.trustedClientsOnline)
    var clients = [];

    if (truestedOnline && truestedOnline.trim() !== "") {
        clients = truestedOnline
            .replace(/[\[\]]/g, "")
            .split(",")
            .map(function(s) {return s.trim()})
            .filter(function(s) {return s.length > 0;});
    }


    if (clients.length > 0) {
        dev[SECURITY].armed = false;
        if (!wasTrustedPresent) {
            wasTrustedPresent = true;
            disarmedClient = clients[0];

            autoEvent = {
                armed: false,
                client: disarmedClient,
                time: now()
            }

            dev[SECURITY].armClient = "";
            dev[SECURITY].disarmClient = autoEvent["client"]
            dev[SECURITY].armTime = autoEvent["time"];
        }

        trustedClients = clients;
        return;
    }

    dev[SECURITY].armed = true;
    if (wasTrustedPresent) {
        wasTrustedPresent = false;
        armedClient = trustedClients[0];

        autoEvent = {
            armed: true,
            client: armedClient,
            time: now()
        }

        dev[SECURITY].armClient = armedClient;
        dev[SECURITY].disarmClient = ""
        dev[SECURITY].armTime = autoEvent["time"];
        trustedClients = [];
    }
}

function now() {
    var d = new Date();

    function pad(n) {
        return (n < 10 ? "0" : "") + n;
    }

    return pad(d.getDate()) + "-" +
        pad(d.getMonth() + 1) + "-" +
        d.getFullYear() + " " +
        pad(d.getHours()) + ":" +
        pad(d.getMinutes());
}
<?php
# Example Call from Router:
# https://<your-domain>/ddns.php?username=%u&password=%p&hostname=%h&ip=%i

require_once('config.php');

addLog();
if(!empty($_REQUEST['username']) && !empty($_REQUEST['hostname']) && !empty($_REQUEST['ip']) ) {
    # Check: Account Exists
    if(array_key_exists($_REQUEST['username'],  $GLOBALS['accounts'])) {
        # Check: Password (unencrypted!)
        if($_REQUEST['password'] == $GLOBALS['accounts'][$_REQUEST['username']]['password']) {
            # Check: Subdomain belong to Account
            if(in_array($_REQUEST['hostname'], $GLOBALS['accounts'][$_REQUEST['username']]['hostnames'])) {
                # Load, modify, write Domain-Zone
                $zone = getZone($GLOBALS['domain']);
                if($_REQUEST['hostname'] == "www") {
                    $zone['main']['address'] = $_REQUEST['ip'];
                } else {
                    $zone = updateZone($zone, $_REQUEST['hostname'], $_REQUEST['ip']);
                }
                $return = putZone($GLOBALS['domain'], $zone);
                if(strpos($return, "SUCCESS") > 0)
                    addLog("SUCCESS");
            }
        }
    }
}
print('OK');

function addLog($extra = "") {
    $msg = date("c") . " - " . getUserIpAddr() . " - " . http_build_query($_REQUEST, '', ' / ');
    if(!empty($extra)) $msg .= " - " . $extra;
    $file = fopen("ddns.log", "a");
    fwrite($file, $msg . PHP_EOL);
    fclose($file);
}

function getUserIpAddr() {
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
        $ip = $_SERVER['HTTP_CLIENT_IP'];
    } elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        $ip = $_SERVER['HTTP_X_FORWARDED_FOR'];
    } else {
        $ip = $_SERVER['REMOTE_ADDR'];
    }
    return $ip;
}

function getZone($domain) {
    $context = stream_context_create(array(
        'http'=>array(
            'method'=>"GET",
            'header' => "Authorization: Basic " . $GLOBALS['token'] . "\r\nX-Domainrobot-Context: " . $GLOBALS['Domainrobot-Context']
    )));
    $data = file_get_contents('https://api.autodns.com/v1/zone/' . $domain, false, $context);
    $data = json_decode($data, true);
    $data = $data['data'][0];
    return $data;
}

function updateZone($zone, $hostname, $ip) {
    $index = $zone['resourceRecords'];
    $index = array_column($index, 'name');
    $index = array_flip($index);
    $hostname_id = $index[$hostname] ?? false;
    if($hostname_id !== false) {
        $zone['resourceRecords'][$hostname_id]['value'] = $ip;
    }
    return $zone;
}

function putZone($domain, $zone) {
    $zone = json_encode($zone);
    $zone = str_replace(',"purgeType":"AUTO"' , '' , $zone);
    $ch = curl_init();
    $headers = array(
        'Content-Type: application/json',
        'Authorization: Basic ' . $GLOBALS['token'],
        'X-Domainrobot-Context: ' . $GLOBALS['Domainrobot-Context']
    );
    curl_setopt($ch, CURLOPT_URL, 'https://api.autodns.com/v1/zone/' . $domain);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 30);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 0);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'PUT');
    curl_setopt($ch, CURLOPT_POSTFIELDS, $zone);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    $ret = curl_exec($ch);
    curl_close($ch);
    return $ret;
}

?>
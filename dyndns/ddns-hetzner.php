<?php
# Example Call from Router:
# https://<your-domain>/ddns-hetzner.php?username=%u&password=%p&hostname=%h&ip=%i
#
# Called without username/hostname/ip: shows a form to generate a password_hash
# value for config.hetzner.php.

require_once('config.hetzner.php');

if(empty($_REQUEST['username']) && empty($_REQUEST['hostname']) && empty($_REQUEST['ip'])) {
    renderPasswordHashTool();
    exit;
}

addLog();
if(!empty($_REQUEST['username']) && !empty($_REQUEST['hostname']) && !empty($_REQUEST['ip'])
    && filter_var($_REQUEST['ip'], FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)) {
    # Check: Account Exists
    if(array_key_exists($_REQUEST['username'],  $GLOBALS['accounts'])) {
        # Check: Password
        if(!empty($_REQUEST['password']) && password_verify($_REQUEST['password'], $GLOBALS['accounts'][$_REQUEST['username']]['password_hash'])) {
            # Check: Subdomain belong to Account
            if(in_array($_REQUEST['hostname'], $GLOBALS['accounts'][$_REQUEST['username']]['hostnames'])) {
                $zoneId = getZoneId($GLOBALS['domain']);
                if($zoneId !== false) {
                    # "www" maps to the zone's root record (Hetzner name "@")
                    $recordName = ($_REQUEST['hostname'] == 'www') ? '@' : $_REQUEST['hostname'];
                    if(rrsetExists($zoneId, $recordName)) {
                        if(setRRSetRecords($zoneId, $recordName, $_REQUEST['ip']))
                            addLog("SUCCESS");
                    }
                }
            }
        }
    }
}
print('OK');

function renderPasswordHashTool() {
    $hash = null;
    if($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($_POST['password'])) {
        $hash = password_hash($_POST['password'], PASSWORD_DEFAULT);
    }
    header('Content-Type: text/html; charset=utf-8');
    ?>
<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><title>DDNS Passwort-Hash generieren</title></head>
<body>
<h1>Passwort-Hash generieren</h1>
<form method="post">
    <input type="password" name="password" placeholder="Neues Passwort" required>
    <button type="submit">Hash erzeugen</button>
</form>
<?php if($hash !== null): ?>
<pre><?= htmlspecialchars($hash, ENT_QUOTES, 'UTF-8') ?></pre>
<?php endif; ?>
</body>
</html>
<?php
}

function addLog($extra = "") {
    $params = $_REQUEST;
    if(isset($params['password'])) $params['password'] = '***';
    $msg = date("c") . " - " . getUserIpAddr() . " - " . http_build_query($params, '', ' / ');
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

function getZoneId($domain) {
    $response = hetznerRequest('GET', 'https://api.hetzner.cloud/v1/zones?name=' . urlencode($domain));
    $data = json_decode($response['body'], true);
    return $data['zones'][0]['id'] ?? false;
}

function rrsetExists($zoneId, $name) {
    $response = hetznerRequest('GET', 'https://api.hetzner.cloud/v1/zones/' . urlencode($zoneId) . '/rrsets/' . urlencode($name) . '/A');
    return $response['code'] === 200;
}

function setRRSetRecords($zoneId, $name, $ip) {
    $body = json_encode(array(
        'records' => array(array('value' => $ip, 'comment' => ''))
    ));
    $url = 'https://api.hetzner.cloud/v1/zones/' . urlencode($zoneId) . '/rrsets/' . urlencode($name) . '/A/actions/set_records';
    $response = hetznerRequest('POST', $url, $body);
    return $response['code'] === 201;
}

function hetznerRequest($method, $url, $body = null) {
    $ch = curl_init();
    $headers = array(
        'Content-Type: application/json',
        'Authorization: Bearer ' . $GLOBALS['hetzner_token']
    );
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 30);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    if($body !== null) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
    }
    $ret = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    return array('code' => $code, 'body' => $ret);
}

?>

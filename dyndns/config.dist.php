<?php
    $GLOBALS['token'] = 'xyz=='; # = base64_encode($username . ':' . $password)
    $GLOBALS['Domainrobot-Context'] = '10'; # 4 = InternetX / 10 = Schlund Tech
    $GLOBALS['domain'] = 'example.com';
    $GLOBALS['accounts'] = Array(
        'user1' => array('password' => 'password1', 'hostnames' => Array('sub1', 'sub2', 'sub3')),
        'user2' => array('password' => 'password2', 'hostnames' => Array('sub4', 'sub5'))
    );
?>
<?php
    $GLOBALS['hetzner_token'] = 'YOUR_HETZNER_API_TOKEN';
    $GLOBALS['domain'] = 'example.com';
    # password_hash: ddns-hetzner.php ohne Parameter aufrufen, um einen Hash zu erzeugen
    $GLOBALS['accounts'] = Array(
        'user1' => array('password_hash' => '$2y$10$REPLACE_WITH_GENERATED_HASH', 'hostnames' => Array('sub1', 'sub2', 'sub3')),
        'user2' => array('password_hash' => '$2y$10$REPLACE_WITH_GENERATED_HASH', 'hostnames' => Array('sub4', 'sub5'))
    );
?>

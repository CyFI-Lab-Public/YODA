<?php
/*
Safe sample
input : use exec to execute the script /tmp/tainted.php and store the output in $tainted
SANITIZE : use preg_replace to keep only char, number and _ ,\, -
construction : use of sprintf via a %s with simple quote
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


$script = "/tmp/tainted.php";
exec($script, $result, $return);

$tainted = $result[0];

$tainted = preg_replace("/[^a-zA-Z0-9_\ -]/", "", $tainted);

$query = sprintf("!name='%s'", $tainted);

$ds = ldap_connect("localhost");
$r = ldap_bind($ds);
$sr = ldap_search($ds, "o=My Company, c=US", $query);
ldap_close($ds);

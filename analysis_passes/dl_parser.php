<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\Node;
  use PhpParser\NodeFinder;
  use PhpParser\NodeTraverser;
  use PhpParser\NodeVisitorAbstract;
  use PhpParser\Node\Expr\ErrorSuppress;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Expr\Assign;
  use PhpParser\Node\Expr\Variable;
  use PhpParser\Node\Scalar\String_;
  use PhpParser\PrettyPrinter;

  $encoded_ast = fgets(STDIN);              /* Read encoded AST from python STDIN pipe */

  /********** Init AST Tools **********/
  $dl_detector = new NodeTraverser;                          /* Traverser to detect FC */
  $finder = new NodeFinder;
  $printer = new PrettyPrinter\Standard;                             /* Pretty Printer */

  $GET_Functions = [
                     'file_get_contents',
                     'wp_remote_get',
                     'http_get'
                   ];

  $CURL_Functions = [
                      'curl_setopt',
                      'curl_exec',
                      'curl_close'
                    ];
  $PUT_Functions = [
                      'file_put_contents',
                      'fread'
                    ];
  
  $GET_Requests = array();
  $CURL_Sessions = array();
  $file_puts = array();
  $assignments_to_find = array();
  $downloaders = array();
  $downloaders2 = array();
  $preg_replace_exists = FALSE;

  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast === null ) { return; }

  function getSpamAssignment($var_name, $line) {                 /* locate assignment node */
    global $finder;
    global $printer;
    global $ast;

    $value = NULL;

    #if( stripos($var_name, 'file') !== FALSE) {
    #  return "not found";
    #}

    $assignments = $finder->findInstanceOf($ast, Assign::class);
    
    foreach ($assignments as $assignment) {              /* check all assignment nodes */
      if ($assignment->var instanceof Node\Expr\Variable) {
        #trigger_error(json_encode("HERE"));
        #trigger_error(json_encode($var_name));
        if (!strcmp($assignment->var->name, $var_name)) {            /* match var name */
          if ($assignment->getLine() <= $line)
            { $value = $assignment; }                     /* update until line reached */
        }
      }
    } 
    
    if ($value) {
      #trigger_error(json_encode("VALUE"));
      #trigger_error(json_encode($value, JSON_PRETTY_PRINT));
      return $value;                                              /* report assignment */
    } else { 
      #trigger_error(json_encode("VALUE NOT FOUND"));
      return 'not found'; }
      
  }
  function getAssignment(Node $var) {  /* trace variable to its most recent assignment */
    global $printer;
    global $finder;
    global $ast;

    $assignments = $finder->find( $ast,
      function(Node $node) use ($var) {
        if( $node->getLine() < $var->getLine() ) {
          if( $node instanceof Assign ) {
            if( $node->var instanceof Variable ) {
              if( strcmp($node->var->name, $var->name) === 0 ) {
                return TRUE;
              }
            } else { return FALSE; }
          } else { return FALSE; }
        } else { return FALSE; }
      }
    );

    if(count($assignments)) {
      $value = end($assignments)->expr;                         /* use last assignment */
      return $printer->prettyPrintExpr($value);
    } else { return $printer->prettyPrintExpr($var); }
  }

  function resolve_imm_arg(Node $a) {
    global $printer;
    if( $a instanceof String_ ) {
      return $printer->prettyPrintExpr($a);
    } else if( $a instanceof Variable ) {
      return $printer->prettyPrintExpr($a);
    } else if ( $a instanceof Node\Scalar\MagicConst) {
        return $a->getName();
    } else if( $a instanceof Node\Expr ) {
      if( $a instanceof Node\Expr\BinaryOp\Concat ) {
        return $printer->prettyPrintExpr($a);
      } else { return 'not found'; }
      
    }
  }
  function resolve(Node $a) {
    global $printer;
    if( $a instanceof String_ ) {
      return $printer->prettyPrintExpr($a);
    } else if( $a instanceof Variable ) {
      return getAssignment($a);
    } else if ( $a instanceof Node\Scalar\MagicConst) {
        return $a->getName();
    } else if( $a instanceof Node\Expr ) {
      if( $a instanceof Node\Expr\BinaryOp\Concat ) {
        return $printer->prettyPrintExpr($a);
      } else { return 'not found'; }
      
    }
  }

  /********** Find calls to preg_replace() in file **********/
  $preg_replace_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $preg_replace_exists;
      
      if( $node instanceof FuncCall ) {
        #if( $node->name instanceof String_ ) {
            if( strcmp($node->name, 'preg_replace') === 0 ) {
              $preg_replace_exists = TRUE;
            } else { }
        #} else { }
      } else { }
    }
  };

  /********** Find all $rv = GET() and all file_put_contents **********/
  $GET_rv_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $GET_Functions;
      global $CURL_Functions;
      global $GET_Requests;
      global $CURL_Sessions;
      global $file_puts;

      if( $node instanceof Assign) {
        if( $node->expr instanceof FuncCall ) {       /* $node => $rv = func($params); */
          if( in_array($node->expr->name, $GET_Functions) ) {/* is func a GET Request? */
            array_push($GET_Requests, $node);
          } else if( strcmp($node->expr->name, 'curl_init') === 0 ) {
            $line = $node->getLine();
            $curl_session = array(                             /* add session to array */
                                    'CODE' => [ $line => $node ],
                                    'URL' =>  ''
                                  );
            $rv = $node->var->name;
            $CURL_Sessions[$rv] = $curl_session;
          } else { }
        } else if( $node->expr instanceof ErrorSuppress ) {
          if( $node->expr->expr instanceof FuncCall ) {
            if( in_array($node->expr->expr->name, $GET_Functions) ) {
              array_push($GET_Requests, $node);
            } else if( strcmp($node->expr->expr->name, 'curl_init') === 0 ) {
              $line = $node->getLine();
              $curl_session = array(                           /* add session to array */
                                    'CODE' => [ $line => $node ],
                                    'URL' =>  ''
                                  );
              $rv = $node->var->name;
              $CURL_Sessions[$rv] = $curl_session;
            } else { }
          } else { }
        } else { }
      } else if( $node instanceof FuncCall ) {
        if( strcmp($node->name, 'file_put_contents') === 0) {
        #trigger_error(json_encode("FUNC CALL"));
        #if( in_array($node->name, $PUT_Functions) ) {/* is func a PUT Request? */
          array_push($file_puts, $node);
        } else if ( in_array($node->name, $CURL_Functions) ) {
          $curl_handle = $node->args[0]->value->name;
          if( array_key_exists($curl_handle, $CURL_Sessions) ) {
            $CURL_Sessions[$curl_handle]['CODE'][$node->getLine()] = $node;
          } else { }
        } else { }
      } else { }
    }
  };

  /********** Detect: file_put_contents($file, $GET_Request) **********/
  $GET_to_PUT_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $GET_Functions;
      global $printer;
      global $downloaders;

      if( $node instanceof FuncCall ) {
        if( strcmp($node->name, 'file_put_contents') === 0 ) {
          $prettyCall = $printer->prettyPrintExpr($node);

          foreach($GET_Functions as $GET_Func) {
            if( strpos($prettyCall, $GET_Func) !== FALSE ) {
              global $finder;
              $getArg = $finder->findFirst($node->args, 
                function( Node $node ) use ($GET_Func) {
                  if( $node instanceof FuncCall ) {
                    if( strcmp($node->name, $GET_Func) === 0 ) {
                      return TRUE;
                    } else { return FALSE; }
                  } else { return FALSE; }
                }
              );

              if( $getArg ) {
                #trigger_error(json_encode($getArg->args[0]->value));
                $url = resolve($getArg->args[0]->value);
              } else { 
                #trigger_error(json_encode($node->args[1]->value));
                $url = resolve($node->args[1]->value); }

              if( stripos($url, 'http') !== FALSE ) {    /* Legitimate URL found -> TP */
                array_push( $downloaders,
                            [ 
                              'CODE'=>[ $node->getLine() => $prettyCall ], 
                              'URL'=> $url
                            ]
                          );
              } else {                        /* check args to see if still interested */
                if( strpos($url, 'functions.php') !== FALSE ) {  /* GET(functions.php) */
                  array_push( $downloaders,
                              [ 
                                'CODE'=>[ $node->getLine() => $prettyCall ], 
                                'URL'=> $url
                              ]
                            );
                } else if( strpos($url, '__FILE__') !== FALSE ) {     /* GET(__FILE__) */
                  global $preg_replace_exists;
                  
                  if( $preg_replace_exists ) {  /* Only TP if preg_replace() is called */
                    array_push( $downloaders,
                                [ 
                                  'CODE'=>[ $node->getLine() => $prettyCall ], 
                                  'URL'=> $url
                                ]
                              );
                  } else { }

                } elseif( strpos($prettyCall, 'md5') !== FALSE ) {          /* PUT MD5 */
                  array_push( $downloaders,
                              [ 
                                'CODE'=>[ $node->getLine() => $prettyCall ], 
                                'URL'=> $url
                              ]
                            );
                }
              }
            }
          }
        } else { }
      } else  { }
    }
  };

  /********** Detect: download_url() **********/
  $download_url_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $printer;
      global $downloaders2;
      global $assignments_to_find;

      if( $node instanceof FuncCall ) {
        if( (strcmp($node->name, 'download_url') === 0 ) or ( strcmp($node->name, 'wp_remote_get') === 0 ) or (strcmp($node->name, 'file_get_contents') === 0 ) or (strcmp($node->name, 'curl_setopt') === 0)) {
          $prettyCall = $printer->prettyPrintExpr($node);
          #trigger_error(json_encode($CURL_Sessions));
          #trigger_error(json_encode($prettyCall));
          #trigger_error(json_encode($node->args));
          #trigger_error("");
          
          if( count($node->args) > 0 ) {
            if ($node->args[0]->value instanceof Node\Expr\Variable) {/* is URL given as a var */
                $url_var_name = $node->args[0]->value->name;         /* trace URL for extraction */
                $url_node = getSpamAssignment($url_var_name, $node->args[0]->getLine());
                #trigger_error(json_encode($url_node));
                if ($url_node) {                                        /* did we find it? */
                  #trigger_error(json_encode("URL NODE"));
                  #trigger_error(json_encode($url_node, JSON_PRETTY_PRINT));
                  $url = cleanURL($url_node);
                  #trigger_error(json_encode($url));
                  $remove_port_vars = '/:\$_{0,1}[[:alnum:]]*\[{0,1}"{0,1}[[:alnum:]]*"{0,1}\]{0,1}\//m';
                  $url = preg_replace($remove_port_vars, '/', $url);   /* remove port vars */
                  #trigger_error(json_encode($url));
                } else { $url = 'not_found';}
            } else if ($node->args[0]->value instanceof Node\Expr) {   /* is URL given directly */
                $url = $node->args[0]->value;                                 /* $url expression */
                
                $url = cleanURL($url);
                $remove_port_vars = '/:\$_{0,1}[[:alnum:]]*\[{0,1}"{0,1}[[:alnum:]]*"{0,1}\]{0,1}\//m';
                $url = preg_replace($remove_port_vars, '/', $url);     /* remove port vars */
            }
            #$url = resolve($node->args[0]->value);
            #$url_temp = resolve($node->args[0]->value);
            #$url = cleanURL($node->args[0]->value);
            #trigger_error(json_encode($url));
          } else { $url = 'not_found';}
          
          if( (stripos($url, 'http') !== FALSE ) or (stripos($url, 'httx') !== FALSE ) or (stripos($url, 'hxxp') !== FALSE )){        /* Legitimate URL found -> TP */
            array_push( $downloaders2,
                        [ 
                          'CODE'=>[ $node->getLine() => $prettyCall ],
                          'URL'=>$url
                        ]
                      );
          } else { }
        }
      }
    }
  };

  /********** preg_replace() check **********/
  $dl_detector->addVisitor($preg_replace_visitor);
  $dl_detector->traverse($ast);
  $dl_detector->removeVisitor($preg_replace_visitor);

  /********** Detect Downloaders **********/
  $dl_detector->addVisitor($GET_rv_visitor);
  $dl_detector->addVisitor($GET_to_PUT_visitor);
  $dl_detector->addVisitor($download_url_visitor);

  $dl_detector->traverse($ast);                                          /* Search AST */

  foreach($file_puts as $put) {                    /* connect source: GET to sink: PUT */
    $putLine = $put->getLine();
    #trigger_error(json_encode("PUT_LINE"));
    #trigger_error(json_encode($putLine));
    $prettyCall = $printer->prettyPrintExpr($put);
    foreach($GET_Requests as $GET_Func) {
      $getLine = $GET_Func->GetLine();
      #trigger_error(json_encode("GET_LINE"));
      #trigger_error(json_encode($getLine));

      if( $getLine <= $putLine ) {
        $rv = $GET_Func->var->name;
        #trigger_error(json_encode("RV"));
        #trigger_error(json_encode($rv));
        #trigger_error(json_encode($prettyCall));
        
        if( strpos($prettyCall, '$'.$rv) !== FALSE ) { /* return value from file_get_contents in an arg to file_put_contents */
          if( $GET_Func->expr instanceof FuncCall) {
            #trigger_error(json_encode($GET_Func->expr->args[0]->value));
            $url = resolve($GET_Func->expr->args[0]->value);
            $imm_arg = resolve_imm_arg($GET_Func->expr->args[0]->value);
          } else if( $GET_Func->expr instanceof ErrorSuppress ) {
            if( $GET_Func->expr->expr instanceof FuncCall ) {
              $url = resolve($GET_Func->expr->expr->args[0]->value);
              $imm_arg = resolve_imm_arg($GET_Func->expr->expr->args[0]->value);
            } else { $url = 'not_found'; }
          } else { $url = 'not_found'; }
          #trigger_error(json_encode("URL"));
          #trigger_error(json_encode($url));

          if( strcmp($url, 'not found') !== 0 ) {

            if( (stripos($url, 'http') !== FALSE ) or (stripos($url, 'httx') !== FALSE ) or (stripos($url, 'hxxp') !== FALSE )){        /* Legitimate URL found -> TP */
              array_push( $downloaders, 
                          [
                            'CODE'=>[
                                      $getLine => $printer->prettyPrintExpr($GET_Func),
                                      $putLine => $prettyCall
                                    ],
                            'URL'=>$url
                          ]
                        );
            } else {                          /* check args to see if still interested */
              if( strpos($url, 'functions.php') !== FALSE ) {    /* GET(functions.php) */
                array_push( $downloaders, 
                            [
                              'CODE'=>[
                                        $getLine => $printer->prettyPrintExpr($GET_Func),
                                        $putLine => $prettyCall
                                      ],
                              'URL'=>$url
                            ]
                          );
              } else if(strpos($imm_arg , '__FILE__') !== FALSE ) {       /* GET(__FILE__) */
              #} else if( strpos($url, '__FILE__') !== FALSE ) {       /* GET(__FILE__) */
                if( $preg_replace_exists ) {    /* Only TP if preg_replace() is called */
                  array_push( $downloaders, 
                              [
                                'CODE'=>[
                                          $getLine => $printer->prettyPrintExpr($GET_Func),
                                          $putLine => $prettyCall
                                        ],
                                'URL'=>$url
                              ]
                            );
                }
              } elseif( strpos($prettyCall, 'md5') !== FALSE ) {            /* PUT MD5 */
                array_push( $downloaders, 
                            [
                              'CODE'=>[
                                        $getLine => $printer->prettyPrintExpr($GET_Func),
                                        $putLine => $prettyCall
                                      ],
                              'URL'=>$url
                            ]
                          );
              }
            }
          }
        }
      }
    }
  }

  function link_url($get_req, $url) {
    $getUrl = "";

    if( $get_req->expr instanceof FuncCall ) {
      $getUrl = $get_req->expr->args[0]->value;
    } else if( $get_req->expr instanceof ErrorSuppres ) {
      $getUrl = $get_req->expr->expr->args[0]->value;
    }

    if( $getUrl instanceof String_ ) {
      if( $url instanceof String_ ) {
        #trigger_error(json_encode($getUrl->value, $url->value));
        return ( strcmp($getUrl->value, $url->value) === 0 );
      }
    } else if( $getUrl instanceof Variable ) {
      if( $url instanceof Variable ) {
        #trigger_error(json_encode($getUrl->name, $url->name));
        return ( strcmp($getUrl->name, $url->name) === 0 );
      }
    } else { }
    return FALSE;
  }

  foreach($CURL_Sessions as $k=>$curl) {
    foreach($curl['CODE'] as $l=>$c){
      $prettyCode = $printer->prettyPrintExpr($c);
      if( strpos($prettyCode, 'CURLOPT_URL') !== FALSE ) {
        $url = $c->args[2]->value;
        #trigger_error(json_encode("URL"));
        #trigger_error(json_encode($url));
        #foreach($GET_Requests as $g) {
        #  if( link_url($g, $url) ) {
        #$curl['CODE'][$g->getLine()] = $printer->prettyPrintExpr($g);
        if( $url instanceof String_ ) {
          $curl['URL'] = $url->value;
        } elseif ($url instanceof Node\Expr) {   /* is URL given directly */
            $url = getAssignment($url);
            #$url = cleanURL($url);
            #trigger_error(json_encode($url));
            $remove_port_vars = '/:\$_{0,1}[[:alnum:]]*\[{0,1}"{0,1}[[:alnum:]]*"{0,1}\]{0,1}\//m';
            $url = preg_replace($remove_port_vars, '/', $url);     /* remove port vars */
            $curl['URL'] = $url;
        } else if( $url instanceof Variable ) {
          #trigger_error(json_encode("HERE1"));
          $url_node = getSpamAssignment($url->name, $url->getLine());
          #trigger_error(json_encode($url_node));
          if ($url_node) {                                        /* did we find it? */
          #  #trigger_error(json_encode("URL NODE"));
          #  #trigger_error(json_encode($url_node, JSON_PRETTY_PRINT));
            $url = cleanURL($url_node);
          #  #trigger_error(json_encode($url));
            $remove_port_vars = '/:\$_{0,1}[[:alnum:]]*\[{0,1}"{0,1}[[:alnum:]]*"{0,1}\]{0,1}\//m';
            $url = preg_replace($remove_port_vars, '/', $url);   /* remove port vars */
          #  #trigger_error(json_encode($url));
          } else { $url = 'not_found';}

          $curl['URL'] = $url;
          #$curl['URL'] = resolve($url);
          #trigger_error(json_encode($curl['URL']));
        } else { $curl['URL'] = 'not found'; };
      }
    #}
  #} 
      $curl['CODE'][$l] = $prettyCode;
      #trigger_error(json_encode($curl['URL'], JSON_PRETTY_PRINT));
    }
    
    if( (stripos($curl['URL'], 'http') !== FALSE ) or (stripos($curl['URL'], 'httx') !== FALSE ) or (stripos($curl['URL'], 'hxxp') !== FALSE )){        /* Legitimate URL found -> TP */
      array_push($downloaders, $curl);
    } else {                                  /* check args to see if still interested */
      if( strpos($curl['URL'], 'functions.php') !== FALSE ) {    /* GET(functions.php) */
        array_push($downloaders, $curl);
      } else if( strpos($curl['URL'], '__FILE__') !== FALSE ) {       /* GET(__FILE__) */
        array_push($downloaders, $curl);
      }
    }
  }

  echo json_encode(                                /* Report results back to Framework */
                    array(
                            'downloaders_1'=>$downloaders,
                            'downloaders_2'=>$downloaders2
                          )
                  ); 

  function cleanURL($url_node) {                    /* make $url node prettyPrint-able */
    global $printer;
    global $finder;

    #trigger_error(json_encode($url_node));
    if ($url_node instanceof Node\Scalar\String_) {
      return $printer->prettyPrintExpr($url_node);
    }
    
    if ( property_exists($url_node, 'expr') ) {
      #trigger_error(json_encode("EXPR"));
      $url = $url_node->expr;
      #trigger_error(json_encode($url, JSON_PRETTY_PRINT));
    } else { $url = $url_node;}

    $URL_Cleaner = new PhpParser\NodeTraverser();

    $resolved = FALSE;
    $cleaner = new class extends PhpParser\NodeVisitorAbstract {  /* convert to string */
      public function enterNode(Node $node) {           
        global $printer;
        global $resolved;

        if ($node instanceof FuncCall)                     /* is $node a function call */
          { 
            #trigger_error(json_encode("FUNC"));
            #trigger_error(json_encode($node));
            return new Node\Scalar\String_($printer->prettyPrintExpr($node)); } 
        elseif ($node instanceof Node\Expr\Variable)                            /* var */
          { 
            #trigger_error(json_encode("VAR"));
            return new Node\Scalar\String_($printer->prettyPrintExpr($node)); }
        elseif ($node instanceof Node\Expr\ArrayDimFetch)                /* array fetch*/
          { 
            #trigger_error(json_encode("STR"));
            #trigger_error(json_encode($node));
            #trigger_error(json_encode(new Node\Scalar\String_($printer->prettyPrintExpr($node)))); 
            return new Node\Scalar\String_($printer->prettyPrintExpr($node)); 
        }
        elseif ($node instanceof Node\Expr\Ternary)                /* ternanry isset cases*/
          { 
            #trigger_error(json_encode("STR"));
            #trigger_error(json_encode($node));
            #trigger_error(json_encode(new Node\Scalar\String_($printer->prettyPrintExpr($node)))); 
            return new Node\Scalar\String_($printer->prettyPrintExpr($node)); 
        }
        elseif ($node instanceof Node\Expr\PropertyFetch)                /* prop fetch */
          { 
            #trigger_error(json_encode("PRP FET"));
            return new Node\Scalar\String_($printer->prettyPrintExpr($node)); }
        else { 
            #trigger_error(json_encode("NONE"));
            #trigger_error(json_encode($node, JSON_PRETTY_PRINT));
            return $node; }
      }
    };

    $URL_Cleaner->addVisitor($cleaner);
    #trigger_error(json_encode($URL_Cleaner));
    $URL_Cleaner->traverse(array($url));                /* clean up func calls in $url */
    #trigger_error(json_encode("CLEANER"));
    #trigger_error(json_encode($url , JSON_PRETTY_PRINT));
    #trigger_error(json_encode($URL_Cleaner->traverse(array($url)), JSON_PRETTY_PRINT));

    try {
      @eval("\$url = " . $printer->prettyPrintExpr($url) . ";");
      #trigger_error("EVAL URL");
      #trigger_error(json_encode($url , JSON_PRETTY_PRINT));
      return $url;
    } catch (Throwable $e) { 
        #trigger_error("EVAL FAILED");
        return "not found";}
    
  }
  /*
    DOWNLOADER ARRAY FORMAT:
      "downloaders_1: (any path from a GET Request to file_put_contents/curl session)
                  {
                    'CODE': {
                              line_number: GET Request,
                              line_number: file_put_contents() call
                            },
                    'URL': extracted_url
                  },
      "downloaders_2: (download_url calls)
                  {
                    'CODE': {
                              line_number: download_url() call
                            },
                    'URL': extracted_url
                  }
  */
?>

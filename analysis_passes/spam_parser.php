<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\NodeFinder;
  use PhpParser\Node;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Expr\Assign;  
  use PhpParser\PrettyPrinter;
  use PhpParser\Error;

  $encoded_ast = fgets(STDIN);              /* Read encoded AST from python STDIN pipe */

  $JsonDecoder = new PhpParser\JsonDecoder();
  $printer = new PrettyPrinter\Standard;  
  $spam_injectors = array();
  
  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast == null ) { return; }
  
  $nodeFinder = new NodeFinder;
  $decoders = $nodeFinder->find($ast, function(Node $node) {
    return ( ($node instanceof FuncCall) 
        and !(@strcmp((string) $node->name, "json_decode")));
  });                                                             /* Find all decoders */

  $assignments = $nodeFinder->find($ast, function(Node $node) {
    return ( ($node instanceof Assign)                /* $rv = func() or $rv = @func() */
              and (($node->expr instanceof FuncCall) 
                or (@$node->expr->expr instanceof FuncCall)) );
  });                                                   /* Find all func_calls with rv */

  foreach ($assignments as $stmt) {          /* retrieve $rv, function name, and $args */
    if ($stmt->expr instanceof FuncCall) {
      $rv = $stmt->var;
      $func = $stmt->expr->name;
      $args = $stmt->expr->args;
    } elseif (@$stmt->expr->expr instanceof FuncCall) {/* is error supressed FuncCall? */
      $rv = $stmt->var;
      $func = $stmt->expr->expr->name;
      $args = $stmt->expr->expr->args;
    }

    #trigger_error(json_encode("RV"));
    #trigger_error(json_encode($rv));

    if (isGetRequest($func))                            /* follow all GET Request rv's */
        { 
            #trigger_error(json_encode("$func"));
            #trigger_error(json_encode("$args"));
            processGetRequest($stmt, $rv, $func, $args); }
  }

  echo json_encode($spam_injectors) ;                           /* echo results to py */

  /******************** End Main() ********************/

  function isGetRequest($func) {                                   /* is $func a GET ? */
    $GET_REQUESTS = array("file_get_contents", "wp_remote_get", "http_get");
    return (in_array( (string) $func, $GET_REQUESTS ));
  }

  function processGetRequest($stmt, $rv, $func, $args=null) {            /* follow $rv */
    global $decoders, $printer;

    foreach ($decoders as $decoder) {                /* is GET's $rv passed to decoder */
      try {
        $arg = $decoder->args[0]->value;
        if ($arg instanceof Node\Expr\ArrayDimFetch) {
          $arg = @(string) $arg->var->name;
        } else { $arg = @(string) $arg->name; }

        if ($rv instanceof Node\Expr\ArrayDimFetch) {
          $rv = @(string) $rv->var->name;
        } else { $rv = @(string) $rv->name; };
      } catch (Throwable $e) {
        continue; /* Something wrong with this statement */
      }
      
      #trigger_error(json_encode($arg));
      #trigger_error(json_encode($rv));
      if (!strcmp($arg, $rv)) {                               /* Report spam injection */
        global $spam_injectors;

        #trigger_error(json_encode("COULD BE SPAM"));
        $get = $printer->prettyPrintExpr($stmt);
        $decode = $printer->prettyPrintExpr($decoder);

        $injector = array( "GET" => $get,        /* set up $injector array for results */
                           "getLine" => $stmt->getLine(),
                           "decoder" => $decode, 
                           "decodeLine" => $decoder->getLine(),
                           "URL" => "not found", 
                           "params" => "None"
                         );

        
        #trigger_error(json_encode("ARGS"));
        #trigger_error(json_encode($args, JSON_PRETTY_PRINT));
        if ($args) {                    /* extract URL and parameters from GET Request */
          if ($args[0]->value instanceof Node\Expr\Variable) {/* is URL given as a var */

            $url_var_name = $args[0]->value->name;         /* trace URL for extraction */
            $url_node = getAssignment($url_var_name, $args[0]->getLine());
            $out_url = cleanStuff($url_node);
            $injector['URL'] = $out_url['URL'];
            $injector['params'] = $out_url['params'];
          } else if ($args[0]->value instanceof Node\Expr) {   /* is URL given directly */
            $url = $args[0]->value;                                 /* $url expression */
            $out_url = cleanStuff($url);
            $injector['URL'] = $out_url['URL'];
            $injector['params'] = $out_url['params'];
          }
        }
        if( $injector['URL'] !== FALSE ) {
          #trigger_error(json_encode($injector["URL"]));
          if(strcmp("not found", $injector["URL"]) !== 0 ) {
            if( array_key_exists('ip', $injector['params']) ) {
              array_push(           /* Only push if URL is found and 'ip' param exists */
                          $spam_injectors,
                          [
                              'URL' => $injector['URL'],
                              'params' => $injector['params']
                          ]
                        ); 
            }
          }
        }
      }
    }
  }
  
  function getAssignment($var_name, $line) {                 /* locate assignment node */
    global $nodeFinder;
    global $printer;
    global $ast;

    $value = NULL;

    if( stripos($var_name, 'file') !== FALSE) {
      return "not found";
    }

    $assignments = $nodeFinder->findInstanceOf($ast, Assign::class);
    
    foreach ($assignments as $assignment) {              /* check all assignment nodes */
      if ($assignment->var instanceof Node\Expr\Variable) {
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
  function cleanStuff($url_node) {                    /* make $url node prettyPrint-able */
    
    $out_url= array( 
                       "URL" => "not found", 
                       "params" => "None"
                     );
    if ($url_node) {                                        /* did we find it? */
      #trigger_error(json_encode("URL NODE"));
      #trigger_error(json_encode($url_node, JSON_PRETTY_PRINT));
      $url = cleanURL($url_node);
      #trigger_error(json_encode($url));
      if( strcmp("not found", $url) !== 0 ) {
        $remove_port_vars = '/:\$_{0,1}[[:alnum:]]*\[{0,1}"{0,1}[[:alnum:]]*"{0,1}\]{0,1}\//m';
        $url = preg_replace($remove_port_vars, '/', $url);   /* remove port vars */
        $url = parse_url($url);
          

        if( $url !== FALSE ) {
          $cleaned = '';

          if( array_key_exists('scheme', $url) ) 
            { $cleaned .= $url['scheme'] . '://'; }
          if( array_key_exists('user', $url) ) { 
            $cleaned .= $url['user']; 
            if( array_key_exists('pass', $url) )
              { $cleaned .= ':' . $url['pass']; }
            $cleaned .= '@';
          }
          if( array_key_exists('host', $url) ) { $cleaned .= $url['host']; }
          if( array_key_exists('port', $url) ) { $cleaned .= ':' . $url['port']; }
          if( array_key_exists('path', $url) ) { $cleaned .= $url['path']; }
          if(  filter_var($cleaned, FILTER_VALIDATE_URL)) 
            { $out_url['URL'] = $cleaned; }
            else { $out_url['URL'] = 'not found'; }                /* avoid FPs */
          if ( array_key_exists('query', $url) ) {
            $params = scrapeParameters(
                                        $cleaned.'?'.$url['query'],
                                        $url_node->getLine()
                                      );
            $out_url['params'] = $params;
          }

        } else { $outr_url['URL'] = 'not found'; }
      
    } else { $out_url['URL'] = 'not found'; }
  } else { $out_url['URL'] = 'not found'; }

  return $out_url;
}

  function cleanURL($url_node) {                    /* make $url node prettyPrint-able */
    global $printer;
    global $nodeFinder;

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

  function scrapeParameters($param_str, $line) {        /* scrape parameters from $url */
    $p = array();

    preg_match_all( '/((\&)|(\?))[a-zA-Z\d_]*\=/m',       /* pattern to extract params */
                    $param_str, 
                    $param
                  );
    
    $value = preg_split( '/((\&)|(\?))[a-zA-Z\d_]*\=/m',  /* pattern to extract params */
                         $param_str,
                         NULL,
                         PREG_SPLIT_NO_EMPTY
                       );

    for ($idx = 0; $idx < count($value); $idx++) {   /* try to resolve variable params */
      if ($value[$idx][0] == '$') { 
        try {
          $assignment = @getAssignment(substr($value[$idx], 1), $line);
          if ($assignment) {
            if (@strcmp($assignment, 'not found') === 0) {
              $value[$idx] = $assignment;
            } else {
              global $printer;
              $value[$idx] = $printer->prettyPrintExpr($assignment);        /* replace */
            }
            
          }
        } catch (Error $e) { }                         /* Couldn't find the assignment */
      }
    }

    for ($idx = 0; $idx < count($param[0]); $idx++)         /* link $params to $values */
      { $p[ substr($param[0][$idx], 1, -1) ] = $value[$idx+1]; }

    return $p;                                          /* report extracted parameters */
  }
?>

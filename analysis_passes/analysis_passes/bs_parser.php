<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\Error;
  use PhpParser\Node;
  use PhpParser\Node\Expr\BinaryOp\Concat;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Expr\Variable;
  use PhpParser\Node\Expr\Assign;
  use PhpParser\Node\Scalar\String_;
  use PhpParser\NodeTraverser;
  use PhpParser\NodeFinder;
  use PhpParser\NodeVisitorAbstract;
  use PhpParser\ParserFactory;
  use PhpParser\PrettyPrinter;

  $encoded_ast = fgets(STDIN);              /* Read encoded AST from python STDIN pipe */
  
  $json_decode_detected = false;
  $detected_links = array();
  $detected_bots = array();
  $bot_user_agents = array("aolbuild", "baiduspider", "bingbot", "msnbot", "duckduckbot", "googlebot", "jeeves/teoma", "yahoo", "yandexbot");
  
  /********** Init AST Tools **********/
  $bs_detector = new NodeTraverser();              /* Traverser to detect Blackhat SEO */
  $finder = new NodeFinder();

  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast == null ) { return; }

  /********** URL Filtering **********/
  function filter_url($url) {
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
        { $url = $cleaned; }
        else { $url = 'not found'; }                /* avoid FPs */
      if ( @array_key_exists('query', $url) ) {
        $params = scrapeParameters(
                                    $cleaned.'?'.$url['query'],
                                    $url_node->getLine()
                                  );
      } else { $params = 'not found'; }

    } else { $url = 'not found'; $params = 'not found'; }

    return ['url' => $url, 'params' => $params];
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

  function getAssignment($var_name, $line) {                 /* locate assignment node */
    global $finder;
    global $printer;
    global $ast;

    $value = NULL;

    if( stripos($var_name, 'file') !== FALSE) {
      return "not found";
    }

    $assignments = $finder->findInstanceOf($ast, Assign::class);
    
    foreach ($assignments as $assignment) {              /* check all assignment nodes */
      if ($assignment->var instanceof Node\Expr\Variable) {
        if (!strcmp($assignment->var->name, $var_name)) {            /* match var name */
          if ($assignment->getLine() <= $line)
            { $value = $assignment; }                     /* update until line reached */
        }
      }
    } 
    
    if ($value) {
      return $value;                                              /* report assignment */
    } else { return 'not found'; }
      
  }

  function handleString($val) {
    /* Does this String refer to some url? */
    $filtered = filter_url($val);
    $url = $filtered['url'];
    if( strcmp($url, 'not found') !== 0 ) {
      global $detected_links;
      array_push(
                  $detected_links, 
                  [
                    'URL' => $url,
                    'Params' => $filtered['params']
                  ]
                );
    }

    /* Does this String contain a bot user agent? */
    global $bot_user_agents;
    foreach ($bot_user_agents as $bot) {
      if (strpos(strtolower($val), $bot) !== false) {
        global $detected_bots;
        array_push($detected_bots, $val);
      }
    }
  }

  function recursiveConcat($node) {
    if ($node->right instanceof String_) {
      if ($node->left instanceof String_) {
        return $node->left->value . $node->right->value;
      } elseif ($node->left instanceof Concat) {
        return recursiveConcat($node->left) . $node->right->value;
      } else {
        return $node->right->value;
      }
    } elseif ($node->right instanceof Concat) {
      if ($node->left instanceof String_) {
        return $node->left->value . recursiveConcat($node->right);
      } elseif ($node->left instanceof Concat) {
        return recursiveConcat($node->left) . recursiveConcat($node->right);
      } else {
        return recursiveConcat($node->right);
      }
    } else {
      if ($node->left instanceof String_) {
        return $node->left->value;
      } elseif ($node->left instanceof Concat) {
        return recursiveConcat($node->left);
      } else {
        return '';
      }
    }
  }

  /********** Detect Blackhat SEO **********/
  $bs_detector->addVisitor(new class extends NodeVisitorAbstract {
    public function enterNode(Node $node) {
      if ($node instanceof Concat) {
        $string = recursiveConcat($node);
        //echo $string . "\r\n";
        handleString($string);
      }

      if ($node instanceof FuncCall) {                     /* is $node a function call */
        if ($node->name == "json_decode") {
          global $json_decode_detected;
          $json_decode_detected = true;
        }
      }
      
      if ($node instanceof String_) {
        handleString($node->value);
      }
    }
  });

  $bs_detector->traverse($ast);

  if (!empty($detected_links) && !empty($detected_bots) && $json_decode_detected) {
    $urls = [];
    foreach( $detected_links as $link ) {
      array_push($urls, $link['URL']);
    }

    $fp = fopen('urls', 'a'); //opens file in append mode 
    fwrite($fp, implode("\n", $urls));
    fwrite($fp, "\n");
    fclose($fp);
    $final_results = array("detected_links" => array_values($detected_links), "detected" => "True");
  } else {
    $final_results = array("detected" => "False");
  }
  
  echo json_encode($final_results) . "\n";

?>

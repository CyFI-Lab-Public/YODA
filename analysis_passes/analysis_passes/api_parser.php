<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\Node;
  use PhpParser\Node\Expr\Assign;
  use PhpParser\Node\Expr\Variable;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Stmt\Function_;
  use PhpParser\NodeFinder;
  use PhpParser\NodeTraverser;
  use PhpParser\NodeVisitorAbstract;
  use PhpParser\PrettyPrinter;

  $encoded_ast = fgets(STDIN);              /* Read encoded AST from python STDIN pipe */

  /********** Init AST Tools **********/
  $abuse_detector = new NodeTraverser;                          /* Finder to detect FC */
  $finder = new NodeFinder;
  $printer = new PrettyPrinter\Standard;
  $out = array(
                'disable_plugins' => [],
                'user_enum' => [],
                'user_insert' => [],
                'check4get' => [],
                'fake_plugin' => [],
                'user_backdoor' => [],
                'post_insert' => [],
                'spam_down' => []
              );

  $dp_nodes = array();
  $ue_nodes = array();
  $uc_nodes = array();
  $c4g_nodes = array();
  $fp_nodes = array();
  $ub_nodes = array();
  $pi_nodes = array();
  $sd_nodes = array();

  $fp_funcs = array(
                      'initiationActivity123',
                      'adminmenuhooking123',
                      'licenseActivationUpdate123',
                      'updatelicenseinfo123',
                      'mainUpdateFunc123',
                      'createRequest',
                      'validateXML',
                      'findPass'
                   );

  $ub_funcs = array(
                      'get_userdata',
                      'get_user_by',
                      'wp_set_current_user',
                      'wp_set_auth_cookie', 
                      'unlink', 
                      'wp_safe_redirect'
                   );
  $pi_funcs = array(                                                         /*Post injection*/
                      'wp_insert_post',
                      'wp_delete_post',
                      'rand',
                      'wp_insert_user', 
                      'wp_update_post', 
                      'get_post'
                   );
  $sd_funcs = array(                                                         /*New spam + downloader*/
                      'curl_init',
                      'curl_setopt',
                      'curl_close',
                      'file_get_contents',
                      'socket_create',
                      'socket_write',
                      'socket_read',
                      'socket_close',
                      'gzinflate',
                      'unserialize',
                      'http_build_query'
                   );

  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast === null ) { return; }

  function get_assignment_node(Node $var) {
    global $finder;
    global $ast;

    $name = $var->name;
    $line = $var->getLine();

    $assignments = $finder->find($ast,
      function (Node $node) use ($name, $line) {
        if( $node->getLine() <= $line ) {
          if( $node instanceof Assign ) {
            if( $node->var instanceof Variable ) {
              if( strcmp($node->var->name, $name) === 0 ) {
                return TRUE;
              } else { return FALSE; }
            } else { return FALSE; }
          } else { return FALSE; }
        } else { return FALSE; } 
      });
      
      return end($assignments)->expr;
  }

  /********** Plugin Disabling **********/
  $dp_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $printer;
      global $dp_nodes;
      
      if( $node instanceof FuncCall) {
        $call = $node->name;                                          /* function name */
        if( $call instanceof Node\Name ) {
          if( strcmp($call, 'update_option') === 0 ) {
            $prettyCall = $printer->prettyPrintExpr($node);
            if( strpos($prettyCall, 'active_plugins') !== FALSE ) {
              if( strpos($prettyCall, '\'\'') !== FALSE ) {
                array_push($dp_nodes, $node);
              } else if( stripos($prettyCall, 'null') !== FALSE ) {
                array_push($dp_nodes, $node);
              } else { }
            } else { }
          } else { }
        }
      } else { }
    }
  };

  /********** User Enumeration **********/
  $ue_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $ue_nodes;

      if( $node instanceof FuncCall ) {
        if( $node->name instanceof Node\Name ) {
          if( strcmp($node->name, 'get_users') === 0 ) {
            if( count($node->args) ) {
              $filter = $node->args[0]->value;

              if( $filter instanceof Variable ) {
                /* trace assignment here */ 
                try {
                  global $printer;
                  $assignment = get_assignment_node($filter);
                  $filter = $printer->prettyPrintExpr($assignment);
                  if( strpos($filter, 'administrator') !== FALSE ) {
                    array_push($ue_nodes, $node);
                  } else { }
                } catch( Throwable $e ) { /* couldn't get assignment node */ }
              } else if( strcmp($filter->getType(), 'Expr_Array') === 0 ) {
                global $printer;
                $filter = $printer->prettyPrintExpr($filter);
                if( strpos($filter, 'administrator') !== FALSE ) {
                  array_push($ue_nodes, $node);
                } else { }
              } else { }
            } else { }
          } else { }
        } else { }
      } else { }
    }
  };
  /********** User Creation **********/
  $uc_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $uc_nodes;

      if( $node instanceof FuncCall ) {
        if( $node->name instanceof Node\Name ) {
          if( strcmp($node->name, 'wp_insert_user') === 0 ) {
            if( count($node->args) ) {
              $filter = $node->args[0]->value;
              if( $filter instanceof Variable ) {
                /* trace assignment here */ 
                try {
                  global $printer;
                  $assignment = get_assignment_node($filter);
                  $user = $printer->prettyPrintExpr($assignment);
                  if( strpos($user, 'administrator') !== FALSE ) {
                    array_push($uc_nodes, $node);
                  } else { }
                } catch( Throwable $e ) { /* couldn't get assignment node */ }
              } else if( strcmp($filter->getType(), 'Expr_Array') === 0 ) {
                global $printer;
                $filter = $printer->prettyPrintExpr($filter);
                if( strpos($filter, 'administrator') !== FALSE ) {
                  array_push($uc_nodes, $node);
                } else { }
              } else { }
            } else { }
          } else { }
        } else { }
      } else { }
    }
  };
  
  /********** Check for GET **********/
  $c4g_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $printer;
      global $c4g_nodes;

      if( $node instanceof FuncCall ) {
        if( $node->name instanceof Node\Name ) {
          if( strcmp($node->name, 'function_exists') === 0 ) {
            $prettyCall = $printer->prettyPrintExpr($node);
            if( strpos($prettyCall, 'file_get_contents') !== FALSE) {
              array_push($c4g_nodes, $node);
            } else { }
          } else { }
        } else { }
      } else { }
    }
  };

  /********** Fake Plugin **********/
  $fp_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $fp_nodes;
      global $fp_funcs;
      
      if( $node instanceof FuncCall ) {
        if( in_array($node->name, $fp_funcs) ) {
          array_push($fp_nodes, $node);
        } else { }
      }

      if( $node instanceof Function_) {
        if( in_array($node->name, $fp_funcs) ) {
          array_push($fp_nodes, $node);
        } else { }
      }
    }
  };

  /********** User Info Based Backdoor **********/
  $ub_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $ub_nodes;
      global $ub_funcs;
      
      if( $node instanceof FuncCall ) {
        if( in_array($node->name, $ub_funcs) ) {
          array_push($ub_nodes, $node);
        } else { }
      }

      if( $node instanceof Function_) {
        if( in_array($node->name, $ub_funcs) ) {
          array_push($ub_nodes, $node);
        } else { }
      }
    }
  };
  /********** Malicious Post Injection  **********/
  $pi_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $pi_nodes;
      global $pi_funcs;
      
      if( $node instanceof FuncCall ) {
        if( in_array($node->name, $pi_funcs) ) {
          array_push($pi_nodes, $node);
        } else { }
      }

      if( $node instanceof Function_) {
        if( in_array($node->name, $pi_funcs) ) {
          array_push($pi_nodes, $node);
        } else { }
      }
    }
  };
  /********** Spam Injection + Downloader  **********/
  $sd_visitor = new class extends NodeVisitorAbstract {
    public function enterNode( Node $node ) {
      global $sd_nodes;
      global $sd_funcs;
      
      if( $node instanceof FuncCall ) {
        if( in_array($node->name, $sd_funcs) ) {
          #trigger_error(json_encode($node, JSON_PRETTY_PRINT));
          array_push($sd_nodes, $node);
        } else { }
      }

      if( $node instanceof Function_) {
        if( in_array($node->name, $sd_funcs) ) {
          array_push($sd_nodes, $node);
        } else { }
      }
    }
  };

  /********** Add Visitors **********/
  $abuse_detector->addVisitor($dp_visitor);
  $abuse_detector->addVisitor($ue_visitor);
  $abuse_detector->addVisitor($uc_visitor);
  $abuse_detector->addVisitor($c4g_visitor);
  $abuse_detector->addVisitor($fp_visitor);
  $abuse_detector->addVisitor($ub_visitor);
  $abuse_detector->addVisitor($pi_visitor);
  $abuse_detector->addVisitor($sd_visitor);

  /********** Traverse AST **********/
  $abuse_detector->traverse($ast);

  /********** Format Results into Output **********/
  foreach($dp_nodes as $node) {
    array_push(
                $out['disable_plugins'],
                $node->getLine() . " : " . $printer->prettyPrintExpr($node)
              );
  }

  foreach($ue_nodes as $node) {
    array_push(
                $out['user_enum'],
                $node->getLine() . " : " . $printer->prettyPrintExpr($node)
              );
  }

  foreach($uc_nodes as $node) {
    array_push(
                $out['user_insert'],
                $node->getLine() . " : " . $printer->prettyPrintExpr($node)
              );
  }

  foreach($c4g_nodes as $node) {
    array_push(
                $out['check4get'],
                $node->getLine() . " : " . $printer->prettyPrintExpr($node)
              );
  }

  foreach($fp_nodes as $node) {
    array_push(
                $out['fake_plugin'],
                $node->getLine() . " : " . $node->name
              );
  }

  foreach($ub_nodes as $node) {
    array_push(
                $out['user_backdoor'],
                $node->getLine() . " : " . $node->name
              );
  }


  foreach($pi_nodes as $node) {
    array_push(
                $out['post_insert'],
                $node->getLine() . " : " . $node->name
              );
  }


  foreach($sd_nodes as $node) {
    array_push(
                $out['spam_down'],
                $node->getLine() . " : " . $node->name
              );
  }
  echo json_encode($out);                                 /* Results back to Framework */
?>

<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\Node;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Stmt\If_;
  use PhpParser\Node\Stmt\Function_;
  use PhpParser\NodeTraverser;
  use PhpParser\NodeVisitorAbstract;
  use PhpParser\PrettyPrinter;

  $encoded_ast = fgets(STDIN);              /* Read encoded AST from python STDIN pipe */

  /********** Init AST Tools **********/
  $err_detector = new NodeTraverser;            /* Traverser to detect error disabling */
  $printer = new PrettyPrinter\Standard;

  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast === null ) { return; }

  $err_disablers = array();
  $err_disabling_funcs = array(
                                'error_reporting(0)',
                                'ini_set(\'error_log\', NULL)',
                                'ini_set(\'log_errors\', 0)',
                                'ini_set(\'display_errors\', \'Off\')'
                              );

  /********** Detect Error Disabling **********/
  function is_disabling_error_reporting( $func_call ) {
    global $err_disabling_funcs;

    if( in_array($func_call, $err_disabling_funcs) ) {
      return TRUE;
    } else { return FALSE; }
  }

  $Err_Disable_Visitor = new class extends NodeVisitorAbstract {

    public function enterNode( Node $node ) {
      if( $node instanceof Function_ ) {                        /* Skip Function Stmts */
        return NodeTraverser::DONT_TRAVERSE_CHILDREN;
      } else if ( $node instanceof If_ ) {                   /* Skip Conditional Stmts */
        return NodeTraverser::DONT_TRAVERSE_CHILDREN;
      } else {
        if( $node instanceof FuncCall ) {                          /* Check Func Calls */
          global $printer;
          $prettyCall = $printer->prettyPrintExpr($node);

          if( is_disabling_error_reporting($prettyCall) ) {
            global $err_disablers;

            $line = $node->getLine();
            $err_disablers[$line] = $prettyCall;
          } else { }
        } else { }
      }
    }

  };

  $err_detector->addVisitor($Err_Disable_Visitor);
  $err_detector->traverse($ast);                                           /* traverse */

  echo json_encode($err_disablers);                        /* report back to framework */
?>
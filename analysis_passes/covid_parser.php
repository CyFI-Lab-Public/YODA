<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\NodeFinder;
  use PhpParser\NodeTraverser;
  use PhpParser\Node;
  use PhpParser\Node\Scalar\String_;
  use PhpParser\Node\Expr\ArrayDimFetch;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Expr\Variable;
  use PhpParser\PrettyPrinter;

  $encoded_ast = fgets(STDIN);              /* Read encoded AST from python STDIN pipe */
  $constructed_funcs = array();

  /********** Init AST Tools **********/
  $covid_detector = new NodeFinder;                          /* Finder to detect Covid */

  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast === null ) { return; }

  /********** Detect COVID WP_VCD **********/
  $global_access = $covid_detector->find( $ast, 
    function(Node $node) {
      return ($node instanceof ArrayDimFetch)
        && ($node->var instanceof Variable)
        && ($node->var->name == "GLOBALS")
        && ($node->dim instanceof String_)
        && ($node->dim->value == "WP_CD_CODE");
    }
  );

  $covid = false;
  if (!empty($global_access)) {$covid = true;}
  
  echo json_encode(array("WP_CD_CODE" => $covid));
?>

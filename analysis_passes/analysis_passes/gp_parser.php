<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\Error;
  use PhpParser\Node;
  use PhpParser\Node\Expr\ArrayDimFetch;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Expr\Variable;
  use PhpParser\Node\Expr\Assign;
	use PhpParser\Node\Scalar\String_;
  use PhpParser\Node\Expr\BinaryOp\Equal;
  use PhpParser\NodeTraverser;
  use PhpParser\NodeDumper;
  use PhpParser\NodeVisitorAbstract;
  use PhpParser\ParserFactory;
  use PhpParser\PrettyPrinter;

  $encoded_ast = fgets(STDIN);                /* Read encoded AST from python STDIN pipe */
  $hash_algos = hash_algos();                 /* array of PHP Hash Algorithm Functions */
  $sus_arrays = array("_REQUEST", "_POST");   /* Arrays possible containing gated strings */
  $sus_keys = array("password");              /* Array of suspicious array keys */
  $gates = array();

  /********** Init AST Tools **********/
  $gp_detector = new NodeTraverser();              /* Traverser to detect Gated Plugin */
  $printer = new PrettyPrinter\Standard;
  
  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast === null ) { return; }

  /********** Detect Plugin Gates **********/
  $gp_detector->addVisitor(new class extends NodeVisitorAbstract {
    public function enterNode(Node $node) {
      if ($node instanceof Equal) {                                /* is $node an '==' */
        global $sus_arrays;
        global $sus_keys;
        if ($node->left instanceof FuncCall) {
          global $hash_algos;
          if (in_array($node->left->name, $hash_algos)){       /* is func a hash_algo? */
            if ($node->right instanceof String_ &&
                preg_match("/[a-f0-9]/", strtolower($node->right->value))){
              global $gates;
              array_push($gates, $node);
            }
          }
        } elseif ($node->right instanceof FuncCall) {
          global $hash_algos;
          if (in_array($node->right->name, $hash_algos)){       /* is func a hash_algo? */
            if ($node->left instanceof String_ &&
                preg_match("/[a-f0-9]/", strtolower($node->left->value))){
              global $gates;
              array_push($gates, $node);
            }
          }
        }
        
        if ($node->left instanceof ArrayDimFetch &&
            $node->left->var instanceof Variable &&
            in_array($node->left->var->name, $sus_arrays) &&
            $node->left->dim instanceof String_ &&
            in_array($node->left->dim->value, $sus_keys)) {
          if ($node->right instanceof String_ &&
                preg_match("/[a-f0-9]/", strtolower($node->right->value))){
            global $gates;
            array_push($gates, $node);
          }
        } elseif ($node->right instanceof ArrayDimFetch &&
                  $node->right->var instanceof Variable &&
                  in_array($node->right->var->name, $sus_arrays) &&
                  $node->right->dim instanceof String_ &&
                  in_array($node->right->dim->value, $sus_keys)) {
          if ($node->left instanceof String_ &&
                preg_match("/[a-f0-9]/", strtolower($node->left->value))){
            global $gates;
            array_push($gates, $node);
          }
        }
      }
    }
  });

  $gp_detector->traverse($ast);
  
  $prettyGates = array();
  foreach($gates as $gate) {
    array_push($prettyGates, $printer->prettyPrintExpr($gate));
  }
	
  echo json_encode( [ 'plugin_gates' => $prettyGates ] );
?>

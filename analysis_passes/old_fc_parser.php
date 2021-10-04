<?php
  require_once __DIR__ . '/vendor/autoload.php';

  use PhpParser\NodeTraverser;
  use PhpParser\NodeVisitorAbstract;
  use PhpParser\Node;
  use PhpParser\Node\Expr\FuncCall;
  use PhpParser\Node\Expr\Variable;
  use PhpParser\Node\Expr\Assign;
  use PhpParser\Node\Expr\ArrayDimFetch;
  use PhpParser\PrettyPrinter;
  
  $encoded_ast = fgets(STDIN);              /* Read encoded AST from python STDIN pipe */
  $constructed_funcs = array();

  /********** Init AST Tools **********/
  $fc_detector = new NodeTraverser();                        /* Traverser to detect FC */
  $fc_resolver = new NodeTraverser();                     /* Traverse to resolve names */
  $fc_replacer = new NodeTraverser();                    /* Traverser to replace names */
  $reverter = new PrettyPrinter\Standard;

  try {                                                                      /* Decode */
    $JsonDecoder = new PhpParser\JsonDecoder();
    $ast = $JsonDecoder->decode($encoded_ast);
  } catch (Throwable $e) { return; } 

  if( $ast == null ) { return; }

  /********** Detect Function Construction **********/
  $fc_detector->addVisitor(new class extends NodeVisitorAbstract {
    public function enterNode(Node $node) {
      if ($node instanceof FuncCall) {                     /* is $node a function call */
        if($node->name instanceof Variable) {                   /* is $name a variable */
          global $constructed_funcs;                  /* note variable name for lookup */
          
          if( !($node->name->name instanceof ArrayDimFetch) ) {
            $var = (string) $node->name->name;
            $constructed_funcs[$var] = NULL;
          }

        } else { /* Ignore call */ }
      }
    }
  });

  /********** Resolve Function Names **********/
  $fc_resolver->addVisitor(new class extends NodeVisitorAbstract {
    public function enterNode(Node $node) {
      if($node instanceof Assign) {
        if($node->var instanceof Variable) {              /* is $node a var assignment */
          global $constructed_funcs;
          $var = $node->var->name;
         
          if( !($var instanceof Variable) ) {   /* is the var one of the funcs we want */
            $keys = array_keys($constructed_funcs);
            if(in_array( $var, $keys )) {
              $expr = $node->expr;
              $constructed_funcs[(string) $node->var->name] = $expr;   /* store expr */
            }            
          }
        }
      }
    }
  });

  /********** Replace Function Names **********/
  $fc_replacer->addVisitor(new class extends NodeVisitorAbstract {
    public function leaveNode(Node $node) {
      global $constructed_funcs;                    /* Replace all names in this array */
      if($node instanceof FuncCall) {                      /* is $node a function call */
        if($node->name instanceof Variable) {                   /* is $node a variable */
          
          $key = $node->name->name;                        /* idx in constructed funcs */
          if(array_key_exists($key, $constructed_funcs)) {                /* true name */  
            $true_name = $constructed_funcs[(string) $node->name->name];
            $name = new Node\Name($true_name);                      /* Create new node */
            $node->name = $name;                           /* Replace name node in AST */
          } else { /* don't have true name, do nothing */ }
        }
      }
    }
  });

  function resolve_names() {
    global $reverter;
    global $constructed_funcs;
    global $argv;
    
    foreach(array_keys($constructed_funcs) as $k) {                /* Revert each name */
      if($constructed_funcs[$k]) {                             /* Was true name found? */
        
        $reverted = $reverter->prettyPrintExpr($constructed_funcs[$k]);
        if( strpos($reverted, "$") === false ) {              /* stmt contains no vars */
          
          try {
            eval("\$v = " . $reverted . ";");               /* construct function name */
          } catch(Throwable $e) {     /* catch any error or exception from eval'd code */
            $v = $reverted;
          }
          $constructed_funcs[$k] = $v;
        } else{ unset($constructed_funcs[$k]); }                   /* remove from list */

      } else { unset($constructed_funcs[$k]); }                    /* remove from list */
    }
  }

  try {
    $fc_detector->traverse($ast);
    $fc_resolver->traverse($ast); resolve_names();
    $fc_replacer->traverse($ast);
  } catch(Exception $e) {
    return(-1);
  }

  $tempfile = "./tmp";
  $reconstructed_code = $reverter->prettyPrintFile($ast);               /* back to php */
  $rv = file_put_contents($tempfile, $reconstructed_code);

  if(!$rv) { echo "Error dumping to tmp file!\n"; return; }
  
  /********** ProgPilot **********/
  $context = new \progpilot\Context;                              /* progpilot context */
  $analyzer = new \progpilot\Analyzer;                          /* taint analysis pass */

  $context->inputs->setFile($tempfile);                          /* configure analysis */
  $context->setConfiguration("./progpilot_config/config.yml");

  $analyzer->run($context);                                      /* run taint analysis */

  /********** Results **********/
  $jsonOutfile = "./results.json";
  $results = $context->outputs->getResults();

  $final_results = array(
                      "constructed" => array_values($constructed_funcs),
                      "progpilot" => $results);

  echo json_encode($final_results, JSON_PRETTY_PRINT) . "\n";

?>

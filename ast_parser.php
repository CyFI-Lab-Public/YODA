<?php
/******************************** MAIN SCRIPT ********************************/
  /* SET UP */
    require './util.php';
    $api_file = "./varsfile.py";
    $wp_functions; 
    $json_arr = array("API" => array(), "Referenced Files" => array());
    get_wp_api();

    $UNARY_OP = array( 12 => "!", 13 => "~", 260 => "@", 261 => "++", 262 => "--" );

    $BINARY_OP = array( 1 => "+", 2 => "-", 3 => "*", 4 => "/", 5 => "%", 6 => "<<",
                      7 => ">>", 8 => ".", 9 => "|", 10 => "&", 11 => "^", 14 => "^^",
                      15 => "===", 16 => "!==", 17 => "==", 18 => "!=", 19 => "<", 20 => "<=", 
                      170 => "<=>", 256 => ">", 257 => ">=", 258 => "||", 259 => "&&", 260 => "??" );

    $CAST_TYPE = array( 1 => "(null)", 4 => "(long)", 5 => "(double)", 6 => "(string)", 7 => "(array)",
                        8 => "(object)", 16 => "(bool)", 17 => "(callable)", 18 => "(iterable)", 19 => "(void)" );
  /* main() */
    //echo "Generating AST for: ".$argv[1]."\n\n";  
    $ast = ast\parse_file($argv[1], $version=50); 
    // var_dump($ast);

    $everything = $ast->children;
    foreach($everything as $e)
      { recursive_search($e); } 

    //$jdata = 
    echo json_encode($json_arr);

    /* EXPORT TO: ast_results.json AND PRETTY PRINT TO SCREEN */
      //$j = fopen("ast_results.json", 'w');
      //fwrite($j, $jdata);
      //fclose($j);
      //$out = shell_exec("python3 -m json.tool ast_results.json");
      //echo "\n".$out."\n";
      
      //return $jdata;
    //echo "\nResults exported to ast_results.json\n";
/*****************************************************************************/
  function json_export($c) {
    global $json_arr;
    
    if($json_arr["API"][$c[0]]) {
      array_push($json_arr["API"][$c[0]], $c[1]);
    } else { /* FIRST OCCURENCE */
      $json_arr["API"][$c[0]] = array();
      array_push($json_arr["API"][$c[0]],$c[1]);  
    }
  }

  function get_wp_api() {        /* GET WP API FUNCTION NAMES FROM $api_file */
    global $api_file, $wp_functions;
    $py_file = fopen($api_file, 'r');

    if($py_file == false) { /* FILE ERROR */
      echo "ERROR: could not open file => ".$api_file;
      exit();
    } else { /* GET LIST */
      $a = false;
      while($a == false) { /* CHECK LINE-BY-LINE */
        $line = fgets($py_file);
        if(substr($line, 0, 10) == "plugin_api") { 
          $a = true; 
        }
      }
      
      $start = strpos($line, "[") + 1;
      $end = strpos($line, "]");
      
      $a = substr($line, $start, $end-$start);
      $wp_functions = explode(',', $a);
      foreach($wp_functions as $idx=>$f) {
        $wp_functions[$idx] = trim($f, " \"");
      }
    } 
    fclose($py_file);
  }

  function wp_api($fname) {       /* CHECK IF FUNCTION ($fname) IS IN WP API */
    global $wp_functions;
    $in_list = false;
    foreach($wp_functions as $c) {  /* CHECK EACH FUNCTION */
      if($fname == $c) { $in_list = true; } /* FLIP TO TRUE IF MATCH */
    }
    return $in_list;
  }

  function recursive_search( $node ) {  /* SEARCH AST FOR CALLS AND INCLUDES */
    global $json_arr;
    if(gettype($node)=="(object)"){
        if($node->kind == 515) {                   /* AST_CALL */
          $f = parse_AST_CALL($node);
          // echo $f[0]."(".$f[1].");\n";
          
          if(wp_api($f[0]))     /* ADD TO ARRAY TO BE EXPORTED */
            { json_export($f); }
        } else if($node->kind == 269) { /* AST_INCLUDE_OR_EVAL */
          switch($node->flags) {
            case 1:  /* EVAL */
              $arg = $node->children["expr"];
              if(gettype($arg) == "object") 
                { $arg = recursive_search($arg); }

              $f = "eval({$arg});\n";
              // echo $f;
              break;
            case 2:  /* INCLUDE */
            case 4:  /* INCLUDE ONCE */
            case 8:  /* REQUIRE */
            case 16: /* REQUIRE ONCE */
              $path = $node->children["expr"];
              if(gettype($path) != "string") 
                { $path = parse_node($path); }

              // echo "REFERENCED_FILE: ".$path."\n";
              array_push($json_arr["Referenced Files"], $path);
              break;
          }
        } else {
          if($node->children) {
            foreach($node->children as $child) 
              { recursive_search($child); }
          }
        }
        }
  }

  function parse_AST_CALL($call) {           /* GET FUNCTION NAME & ARG LIST */
    if($call->children["expr"])              /* FUNCTION NAME */
      { $name = $call->children["expr"]->children["name"]; }

    if($call->children["args"]) {            /* ARG_LIST */
      $arg_list = $call->children["args"]->children;
      $args = "";
      if(count($arg_list) > 0) {
        foreach($arg_list as $arg) {         /* GET EACH ARG */
          $arg_type = gettype($arg);
          if($arg_type != "object") {        /* PRINTABLE ARG */
            if(gettype($arg) == "string")
              { $arg = "'".$arg."'"; }
            $args = $args.$arg.", ";
          } else {                           /* ast\Node */
              $arg = parse_node($arg);
              $args = $args.$arg.", ";
          }
        } 
      } else { $args = ""; }                 /* NO PARAMETERS TO FUNCTION */
      $args = rtrim($args, ", ");
    }
    return array($name, $args);
  }

  function parse_node($node) { /* CALL APPROPRIATE PARSER BASED ON NODE KIND */
    switch($node->kind) {
      case 0:   /* AST_MAGIC_CONST */
        $node = parse_AST_MAGIC_CONST($node);
        break;
      
      case 130: /* AST_ARRAY */
        $node = parse_AST_ARRAY($node);
        break;

      case 131: /* AST_ENCAPS_LIST */
        $node = parse_AST_ENCAPS_LIST($node);
        break;

      case 270: /* AST_UNARY_OP */
        $node = parse_AST_UNARY_OP($node);
        break;

      case 256: /* AST_VAR */
        $node = parse_AST_VAR($node);
        break;

      case 257: /* AST_CONST */
        $node = parse_AST_CONST($node); 
        break;

      case 261: /* AST_CAST */
        $node = parse_AST_CAST($node);
        break;

      case 512: /* AST_DIM */
        $node = parse_AST_DIM($node);
        break;

      case 513: /* AST_PROP */
        $node = parse_AST_PROP($node);
        break;

      case 515: /* AST_CALL */
        $node = parse_AST_CALL($node);
        $node = $node[0]."({$node[1]})";
        break;
      
      case 520: /* AST_BINARY_OP */
        $node = parse_AST_BINARY_OP($node);
        if(gettype($node) == "object") {
          $node = "<AST_BINARY_OP: ".$node->flags.">";
        }
        break;

      case 768: /* AST_METHOD_CALL */
        $node = parse_AST_METHOD_CALL($node);
        break;

      case 769: /* AST_STATIC_CALL */
        $node = parse_AST_STATIC_CALL($node);
        break;

      case 770: /* AST_CONDITIONAL */
        $node = parse_AST_CONDITIONAL($node);
        break;

      default:  // unrecognized, echo so we can find it
        $node = "<".ast\get_kind_name($node->kind).">";
        break;
    } return $node;
  }

  function parse_AST_MAGIC_CONST($head) {             /* RESOLVE MAGIC CONST */
    switch($head->flags) {
      case 370: /* MAGIC_LINE */
        $const = "__LINE__";
        break;

      case 371: /* MAGIC_FILE */
        $const = "__FILE__";
        break;

      case 372: /* MAGIC_DIR */
        $const = "__DIR__";
        break;

      default: // echo so we know to add it
        $const = "<AST_MAGIC_CONST: ".$arg->flags.">"; 
    }
    return $const;
  }

  function parse_AST_ARRAY($head) {                        /* RESOLVE ARRAYS */
    if(!count($head->children)) /* EMPTY ARRAY */
      { return "array()"; }
    
    $element_list = "";
    foreach($head->children as $element) {
      $key = $element->children["key"];
      $val = $element->children["value"];

      if(gettype($val) == "object")
        { $val = parse_node($val); }

      if($key) {
        if(gettype($key) == "object") // not sure if this is needed
          { $key = parse_node($key); }  // but better safe than sorry ?
        $e = " '{$key}' => {$val}"; 
      } else {
        $e = " {$val}";
      }
      $element_list = $element_list.$e.",";
    } $element_list = trim(rtrim($element_list, ","));

    return "array($element_list)";
  }

  function parse_AST_ENCAPS_LIST($head) {    /* RESOLVE ENCAPSULATED STRINGS */
    $list = $head->children;

    $str = "";
    foreach($list as $i) {
      if(gettype($i) == "object") {
        $i = parse_node($i);
        $str .= "{".$i."}";
      } else {
        if($i == "\n")
          { $i = "\\n"; }
        $str .= $i;
      }
    } $str = "\"$str\"";
    
    return $str;
  }

  function parse_AST_UNARY_OP($head) {           /* RESOLVE UNARY OPERATIONS */
    global $UNARY_OP;
    $op = $UNARY_OP[$head->flags];

    $operand = $head->children["expr"];
    if(gettype($operand) == "object")
      { $operand = parse_node($operand); }

    return $op.$operand;
  }

  function parse_AST_VAR($head) {                  /* RESOLVE VARIABLE NAMES */
    $v = $head->children["name"];
    if(gettype($v) == "object")
      { $v = parse_node($v); }

    return "$".$v;
  }

  function parse_AST_CONST($head) {                   /* RESOLVE CONST NAMES */
    $a = $head->children["name"]->children["name"];
    if(gettype($a) == "object")
      { $a =  parse_node($a); }
    return $a;
  }

  function parse_AST_CAST($head) {                        /* RESOLVE CASTING */
    global $CAST_TYPE;
    $type = $CAST_TYPE[$head->flags];

    $expr = $head->children["expr"];
    if(gettype($expr) == "object") 
      { $expr = parse_node($expr); }

    return "$type {$expr}";
  }

  function parse_AST_DIM($head) {                            /* RESOVLE DIMS */
    $expr = $head->children["expr"];
    if(gettype($expr) == "object")
      { $expr = parse_node($expr); }

    $dim = $head->children["dim"];
    if(gettype($dim) == "object")
      { $dim = parse_node($dim); }

    return $expr."[{$dim}]";
  }

  function parse_AST_PROP($head) {                     /* RESOLVE PROPERTIES */
    $expr = $head->children["expr"];
    if(gettype($expr) == "object")
      { $expr = parse_node($expr); }
    
    $prop = $head->children["prop"];
    if(gettype($prop) == "object")
      { $prop = parse_node($prop); }
    
    return "{$expr}->{$prop}";
  }

  function parse_AST_BINARY_OP($head) {         /* RESOLVE BINARY OPERATIONS */
    global $BINARY_OP;
    $operator = $BINARY_OP[$head->flags];    

    /* GET LEFT AND RIGHT */
    $left = $head->children["left"];
    if(gettype($left) == "string")
      { $left = "'$left'"; }
    if(gettype($left) == "object") 
      { $left = parse_node($left); }

    $right = $head->children["right"];
    if(gettype($right) == "string")
      { $right = "'$right'"; }
    if(gettype($right) == "object") 
      { $right = parse_node($right); }

    /* RECONSTRUCT STATEMENT */
    $op = "$left $operator $right";
    return $op;
  }

  function parse_AST_METHOD_CALL($head) {            /* RESOLVE METHOD CALLS */
    $expr = $head->children["expr"];
    $method = $head->children["method"];
    $arg_list = $head->children["args"]->children;

    if(gettype($expr) == "object")
      { $expr = parse_node($expr); }
    if(gettype($expr) == "array")
      { $expr = $expr[0]."({$expr[1]})"; }

    if(gettype($method) == "object")
      { $method = parse_node($method); }

    /* PARSE ARG_LIST */
    if(count($arg_list) > 0) {
      foreach($arg_list as $arg) {    /* GET EACH ARG */
        $arg_type = gettype($arg);
        if($arg_type != "object") {   /* PRINTABLE ARG */
          if(gettype($arg) == "string")
            { $arg = "'".$arg."'"; }
          $args = $args.$arg.", ";
        } else {                      /* ast\Node */
            $arg = parse_node($arg);
            $args = $args.$arg.", ";
        }
      } $args = rtrim($args, ", ");
    } else { /* NO PARAMETERS TO FUNCTION */
      $args = "";
    }

    return "$expr->$method({$args})";
  }

  function parse_AST_STATIC_CALL($head) {            /* RESOLVE STATIC CALLS */
    $class = $head->children["class"]->children["name"];
    $method = $head->children["method"];
    $arg_list = $head->children["args"]->children;
    $args = "";
    if(count($arg_list) > 0) {
      foreach($arg_list as $arg) {    /* GET EACH ARG */
        $arg_type = gettype($arg);
        if($arg_type != "object") {   /* PRINTABLE ARG */
          if(gettype($arg) == "string")
            { $arg = "'".$arg."'"; }
          $args = $args.$arg.", ";
        } else {                      /* ast\Node */
            $arg = parse_node($arg);
            $args = $args.$arg.", ";
        }
      } $args = rtrim($args, ", ");
    } else { /* NO PARAMETERS TO FUNCTION */
      $args = "";
    }

    $static_call = "$class::$method({$args})";
    return $static_call;
  }

  function parse_AST_CONDITIONAL($head) {              /* RESOLVE CONDITIALS */
    $c = $head->children["cond"]; /* GET CONDITION */
    if(gettype($c) == "object")
      { $c = parse_node($c); }
    
    $t = $head->children["true"]; /* GET TRUE ASSIGNMENT */
    if(gettype($t) == "object")
      { $t = parse_node($t); }
    if(gettype($t) == "string")
      { $t = "'{$t}'"; }

    $f = $head->children["false"]; /* GET FALSE ASSIGNENT */
    if(gettype($f) == "object")
      { $f = parse_node($f); }
    if(gettype($f) == "string")
      { $f = "'{$f}'"; }

    return "{$c} ? {$t} : {$f}";  /* RECONSTRUCT TERNARY */
  }
?>

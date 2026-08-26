import tree_sitter_python
import tree_sitter_javascript
from tree_sitter import Language, Parser
import os

class ParserService:
    def __init__(self):
        self.parsers = {}
        
        # Initialize Python Parser
        py_lang = Language(tree_sitter_python.language())
        py_parser = Parser(py_lang)
        self.parsers['.py'] = py_parser
        
        # Initialize JavaScript Parser
        js_lang = Language(tree_sitter_javascript.language())
        js_parser = Parser(js_lang)
        self.parsers['.js'] = js_parser
        self.parsers['.ts'] = js_parser  # Use JS parser for TS basics in MVP

    def parse_file(self, filename: str, code: str) -> dict:
        ext = os.path.splitext(filename)[1]
        parser = self.parsers.get(ext)
        
        result = {
            "filename": filename,
            "language": ext,
            "classes": [],
            "functions": [],
            "raw_code": code # Fallback
        }
        
        if not parser:
            return result # If language not supported, we just return raw code
            
        tree = parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node
        
        # A simple tree walk to find functions and classes
        self._find_symbols(root_node, code, result)
        
        return result
        
    def _find_symbols(self, node, code, result):
        if node.type in ['class_definition', 'class_declaration']:
            # Try to grab the class name
            name_node = node.child_by_field_name('name')
            if name_node:
                result['classes'].append(code[name_node.start_byte:name_node.end_byte])
        
        elif node.type in ['function_definition', 'function_declaration', 'method_definition']:
            name_node = node.child_by_field_name('name')
            if name_node:
                result['functions'].append(code[name_node.start_byte:name_node.end_byte])
                
        for child in node.children:
            self._find_symbols(child, code, result)

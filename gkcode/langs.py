# -*- coding: utf-8 -*-
"""Ngôn ngữ bổ sung của GKcode 4.4: C#, TypeScript, Rust, Kotlin, Lua, PHP, Ruby, CSS, HTML/XML,
YAML, TOML, INI, SQL. Đăng ký vào các bảng dùng chung (EXT_TO_LANG, LANG_CFG, KEYWORDS, ...)."""
import importlib as _il
for _n in ['common', 'core', 'theme', 'editor']:
    globals().update({k: v for k, v in vars(_il.import_module(__package__ + "." + _n)).items()
                      if not k.startswith("__")})
del _il, _n

_NOCFG = dict(line=None, block=False, triple=(), backtick=False, preproc=False, brace=False,
              indent="  ")


def _lang(key, label, exts, cfg, kws=(), run=None, snippets=None):
    for e in exts:
        EXT_TO_LANG[e] = key
        TEXT_EXTS.add(e)
    LANGUAGE_LABELS[key] = label
    LANG_EXT[key] = exts[0]
    LANG_CFG[key] = cfg
    KEYWORDS[key] = list(dict.fromkeys(kws))
    if snippets:
        SNIPPETS.setdefault(key, {}).update(snippets)
    if run:
        RUN_TEMPLATES[key] = {"steps": run, "need": []}
        RUNNABLE.add(key)


def _first_tool(*cands):
    """cands: (tên_tool, [args...]) -> (đường dẫn, args) của tool đầu tiên có sẵn."""
    for name, args in cands:
        p = find_tool(name)
        if p:
            return p, args
    return None, None


# C-like
_lang("csharp", "C#", [".cs"], dict(_C_LIKE, preproc=True, triple=('"""',)),
      "abstract as base bool break byte case catch char checked class const continue decimal default "
      "delegate do double else enum event explicit extern false finally fixed float for foreach goto if "
      "implicit in int interface internal is lock long namespace new null object operator out override "
      "params private protected public readonly ref return sbyte sealed short sizeof stackalloc static "
      "string struct switch this throw true try typeof uint ulong unchecked unsafe ushort using virtual "
      "void volatile while var async await record init required get set yield nameof Console String List "
      "Dictionary Task".split(),
      run=[("Chạy (dotnet run)", "dotnet", ["run", "{file}"])] if find_tool("dotnet") else None,
      snippets={"main": 'using System;\n\nclass Program\n{\n    static void Main()\n    {\n        Console.WriteLine("$0");\n    }\n}',
                "cw": "Console.WriteLine($0);", "prop": "public $0 { get; set; }"})

_JS_KW = KEYWORDS.get("javascript", [])
_ts_run = _first_tool(("tsx", ["{file}"]), ("ts-node", ["{file}"]), ("bun", ["run", "{file}"]),
                      ("deno", ["run", "-A", "{file}"]))
_lang("typescript", "TypeScript", [".ts", ".tsx", ".mts", ".cts"], dict(_C_LIKE, backtick=True),
      _JS_KW + "interface type enum implements namespace declare readonly abstract private protected "
      "public static as is keyof infer never unknown any string number boolean symbol bigint object "
      "satisfies override".split(),
      run=[("Chạy (%s)" % os.path.basename(_ts_run[0]), _ts_run[0], _ts_run[1])] if _ts_run[0] else None,
      snippets={"log": "console.log($0);", "iface": "interface $0 {\n    \n}",
                "fn": "function $0(): void {\n    \n}"})

_lang("rust", "Rust", [".rs"], dict(_C_LIKE),
      "as async await break const continue crate dyn else enum extern false fn for if impl in let loop "
      "match mod move mut pub ref return self Self static struct super trait true type unsafe use where "
      "while i8 i16 i32 i64 i128 isize u8 u16 u32 u64 u128 usize f32 f64 bool char str String Vec Option "
      "Some None Result Ok Err Box println print format vec panic".split(),
      run=[("Biên dịch (rustc)", "rustc", ["{file}", "-o", "{exe}"]), ("Chạy chương trình", "{exe}", [])]
      if find_tool("rustc") else None,
      snippets={"main": 'fn main() {\n    println!("$0");\n}', "pl": 'println!("{}", $0);'})

_lang("kotlin", "Kotlin", [".kt", ".kts"], dict(_C_LIKE),
      "abstract as break by catch class companion const continue data do else enum false final finally for "
      "fun if in init inline interface internal is lateinit null object open operator out override package "
      "private protected public return sealed super suspend this throw true try typealias val var when "
      "while Int String Boolean Double Float Long List Map println".split(),
      snippets={"main": 'fun main() {\n    println("$0")\n}'})

_lang("php", "PHP", [".php"], dict(_C_LIKE, block=True),
      "abstract and array as break case catch class clone const continue declare default do echo else "
      "elseif empty enddeclare endfor endforeach endif endswitch endwhile extends final finally fn for "
      "foreach function global if implements include include_once instanceof interface isset list match "
      "namespace new or print private protected public readonly require require_once return static "
      "switch throw trait try unset use var while xor yield true false null".split(),
      run=[("Chạy (php)", "php", ["{file}"])] if find_tool("php") else None)

_lang("ruby", "Ruby", [".rb"], dict(_NOCFG, line="#", indent="  "),
      "alias and begin break case class def do else elsif end ensure false for if in module next "
      "nil not or redo rescue retry return self super then true undef unless until when while yield "
      "puts require attr_accessor attr_reader attr_writer".split(),
      run=[("Chạy (ruby)", "ruby", ["{file}"])] if find_tool("ruby") else None)

_lang("lua", "Lua", [".lua"], dict(_NOCFG, line="--", indent="  "),
      "and break do else elseif end false for function goto if in local nil not or repeat return then "
      "true until while print require pairs ipairs table string math".split(),
      run=[("Chạy (lua)", "lua", ["{file}"])] if find_tool("lua") else None)

# markup / style / config
_lang("css", "CSS / SCSS", [".css", ".scss", ".less"],
      dict(_NOCFG, block=True, css=True, brace=True, indent="    "),
      "important inherit initial unset auto none block inline flex grid absolute relative fixed sticky "
      "solid dashed dotted transparent @media @import @keyframes @font-face @supports @mixin @include "
      "@extend @use".split(),
      snippets={"flex": "display: flex;\n    align-items: center;\n    justify-content: $0;"})

_html_cfg = dict(_NOCFG, markup=True, html_comment=True, brace=False, indent="  ")
_html_run = [("Mở trình duyệt", sys.executable, ["-m", "webbrowser", "{file}"])] \
    if not getattr(sys, "frozen", False) else None
_lang("html", "HTML / XML", [".html", ".htm", ".xhtml", ".svg", ".xml", ".xaml", ".vue"], _html_cfg,
      (), run=_html_run,
      snippets={"html5": '<!DOCTYPE html>\n<html lang="vi">\n<head>\n  <meta charset="utf-8">\n'
                         '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
                         '  <title>$0</title>\n</head>\n<body>\n  \n</body>\n</html>'})

_lang("yaml", "YAML", [".yml", ".yaml"], dict(_NOCFG, line="#"), "true false null yes no on off".split())
_lang("toml", "TOML", [".toml"], dict(_NOCFG, line="#"), "true false".split())
_lang("ini", "INI / Config", [".ini", ".cfg", ".conf", ".properties"], dict(_NOCFG, line="#"), ())
_lang("sql", "SQL", [".sql"], dict(_NOCFG, line="--", block=True, indent="    "),
      "select from where insert into values update set delete create table drop alter add column index "
      "primary key foreign references join inner left right outer on group by order having limit offset "
      "distinct union all as and or not null is in like between exists case when then else end count sum "
      "avg min max asc desc begin commit rollback view trigger SELECT FROM WHERE INSERT INTO VALUES UPDATE "
      "SET DELETE CREATE TABLE DROP ALTER JOIN ON GROUP BY ORDER HAVING LIMIT AND OR NOT NULL AS".split())

# C++ : bổ sung từ khóa hiện đại cho C / C++ (tô màu đầy đủ hơn)
KEYWORDS["cpp"] = list(dict.fromkeys(KEYWORDS.get("cpp", []) + [
    "constexpr", "consteval", "constinit", "noexcept", "nullptr", "decltype", "static_assert",
    "thread_local", "concept", "requires", "co_await", "co_yield", "co_return", "override", "final",
    "std", "string", "vector", "map", "unordered_map", "set", "shared_ptr", "unique_ptr",
    "make_shared", "make_unique", "cout", "cin", "endl", "auto", "using", "namespace", "template",
    "typename", "virtual", "explicit", "friend", "operator"]))
for _e, _l in ((".hh", "cpp"), (".hxx", "cpp"), (".ipp", "cpp"), (".c++", "cpp"), (".h++", "cpp"),
               (".ixx", "cpp"), (".cppm", "cpp"), (".jsx", "javascript"), (".cjs", "javascript"),
               (".jsonc", "json"), (".json5", "json"), (".geojson", "json"), (".webmanifest", "json")):
    EXT_TO_LANG[_e] = _l
    TEXT_EXTS.add(_e)

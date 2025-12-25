

# **Machine Command DSL Reference**

This document describes the full syntax and behavior of the custom DSL used to define machine‑interface actions, read‑patterns, and behavior mappings across multiple firmware interfaces.


# **Machine Command DSL — Specification**

This DSL defines how machine‑interface commands, behaviors, and read‑patterns are written inside the YAML configuration.  
It applies to:

- `actions.format`
- `actions.info`
- `actions.type`
- `read.format`
- `read.info`
- `read.type`
- `behavior.format`
- `behavior.info`
- `behavior.type`

The DSL is evaluated at runtime to generate commands or extract values from device responses.

---

## **1. Parameter Substitution**

### **Basic substitution**
```
{param}
```
Replaces the placeholder with the value of parameter `param`.

**Example**  
`X{x}` → `X20.3` when `x = 20.3`.

---

## **2. Action Reference Substitution**

### **Same‑interface reference**
```
{actionName}
```
Replaces with the *format* of `actionName` for the current interface.

### **Cross‑interface reference**
```
{actionName(interfaceId)}
```
Replaces with the format of `actionName` for the specified interface ID.

---

## **3. Special Character Insertion**

### **Decimal**
```
{char(##)}
```

### **Hexadecimal**
```
{char(0x##)}
```

Inserts the UTF‑8 character for the given code.

**Example**  
`{char(0x18)}` → Ctrl+X

---

## **4. Optional Segments**

Optional blocks are enclosed in brackets:

```
[ ... ]
```

They are included **only if at least one parameter inside `{}` exists**.

### **Examples**

`test[ X{x}]`  
- If `x = "_x"` → `"test X_x"`  
- If `x` missing → `"test"`

`test[ X]`  
- No `{}` inside → always ignored → `"test"`

---

## **5. OR‑Selection Between Optional Segments**

```
[opt1{param}]||[opt2{param}]
```

The first block whose parameters exist is used.

**Example**

`[X{y}]||[X{x}]`  
- If `y = 5` → `"X5"`  
- Else if `x = 3` → `"X3"`  
- Else if `y = 5` and `x = 3` → `"X5"` 
- Else → nothing

---

## **6. Required Optional Groups**

```
[&&(N)]
```

Requires **at least N optional blocks following it** to have valid parameters.

### **Examples**

`[&&(1)][X{X}]||[X{x}]`  
- If neither `X` nor `x` exists → **error**

`[&&(1)][X{X}][Y{Y}]`  
- Requires at least one of `X` or `Y`  
- If both missing → **error**

---

## **7. Newline Support**

```
\n
```

Allows multi‑line command sequences. Very useful for Macros or sequences.

**Example**

```
{unlockAlarm}\nG92 X0 Y0 Z0
```

---

## **8. **Shared metadata**

```
*(id)
```

Uses the same format/info/type values from another interface ID for the same command.

### **Info and Type Metadata**

Each action may have:

- `info` → human‑readable description  
- `type` → type information  

These are optional.
 
---

## **9. Read‑Pattern DSL (Regex Extraction)**

Used to extract values from device responses.

### **Regex block**

```
<r'regex_pattern'[group{param}]>
```

- If the pattern starts with `r'...'`, it is treated as a Python regex.
- Otherwise, it is treated as a literal string.

### **Group extraction**

```
[#{param}]
```

- `#` = regex group number  
- `param` = name to store the extracted value  

**Example**

```
<r'XPos:([+-]?[0-9]*[.][0-9]+)'[1{Xpos}]>
```

Extracts the first match group into parameter `Xpos`.

### **Validation**

- Invalid regex → no data extracted  
- Test patterns at https://pythex.org/

---

## **10. Required Read Parameters**

The read routine expects at least one of:

- `ACK`
- `STATUS`
- `STATE_XYZ`
- `XPOS`, `YPOS`, `ZPOS`

Unrecognized commands are logged.

---

## **11. Behavior Section Rules**

- Defines interface‑specific behavior logic.
- Uses the same `format / info / type` structure.
- Optional parameters are **not allowed** here.
- Values are read as text and then converted.

---

# **DSL Cheat Sheet**

A compact reference for quick use.

---

## **Substitution**
- `{param}` → insert parameter  
- `{actionName}` → insert action format (same interface)  
- `{actionName(2)}` → insert action format from interface 2  
- `{char(10)}` → LF  
- `{char(0x18)}` → Ctrl+X  

---

## **Optional Blocks**
- `[ X{x}]` → included only if `x` exists  
- `[opt1{p}]||[opt2{p}]` → OR selection  
- `[&&(1)]` → require at least 1 valid optional block  

---

## **Regex Read Patterns**
- `<r'pattern'[1{param}]>` → extract group 1  
- `<'literal'[1{param}]>` → literal match  
- `[#{param}]` → group extraction  

---

## **Newlines**
- `\n` → multi‑line commands  

---

## **Metadata**
- `*(id)` → reuse format/info/type from interface `id`  

---

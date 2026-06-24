package com.fr.function;

import com.fr.script.AbstractFunction;

/** FineReport custom function: decimalToChinese(a money amount). */
public class decimalToChinese extends AbstractFunction {

    @Override
    public Object run(Object[] args) {
        if (args == null || args.length == 0 || args[0] == null) {
            return "";
        }
        return ChineseConvertUtil.decimalToChinese(args[0]);
    }
}

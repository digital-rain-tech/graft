package com.fr.function;

import com.fr.script.AbstractFunction;

/** FineReport custom function: numberToChinese(an integer). */
public class numberToChinese extends AbstractFunction {

    @Override
    public Object run(Object[] args) {
        if (args == null || args.length == 0 || args[0] == null) {
            return "";
        }
        return ChineseConvertUtil.numberToChinese(args[0]);
    }
}

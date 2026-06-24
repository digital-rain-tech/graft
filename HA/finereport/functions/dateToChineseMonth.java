package com.fr.function;

import com.fr.script.AbstractFunction;

/** FineReport custom function: dateToChineseMonth(a date). */
public class dateToChineseMonth extends AbstractFunction {

    @Override
    public Object run(Object[] args) {
        if (args == null || args.length == 0 || args[0] == null) {
            return "";
        }
        return ChineseConvertUtil.dateToChineseMonth(args[0]);
    }
}

package com.fr.function;

import com.fr.script.AbstractFunction;

/** FineReport custom function: dateToChineseYear(a date). */
public class dateToChineseYear extends AbstractFunction {

    @Override
    public Object run(Object[] args) {
        if (args == null || args.length == 0 || args[0] == null) {
            return "";
        }
        return ChineseConvertUtil.dateToChineseYear(args[0]);
    }
}

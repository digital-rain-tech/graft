package com.fr.function;

import com.fr.script.AbstractFunction;

/** FineReport custom function: dateToChineseDay(a date). */
public class dateToChineseDay extends AbstractFunction {

    @Override
    public Object run(Object[] args) {
        if (args == null || args.length == 0 || args[0] == null) {
            return "";
        }
        return ChineseConvertUtil.dateToChineseDay(args[0]);
    }
}

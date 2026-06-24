package com.fr.function;

import com.fr.script.AbstractFunction;

/** FineReport custom function: lastIndexOf(text, search[, fromIndex]) — 0-indexed. */
public class lastIndexOf extends AbstractFunction {

    @Override
    public Object run(Object[] args) {
        if (args == null || args.length < 2 || args[0] == null || args[1] == null) {
            return -1;
        }
        String text = String.valueOf(args[0]);
        String search = String.valueOf(args[1]);
        int from = args.length > 2 && args[2] != null
                ? (int) Math.floor(Double.parseDouble(String.valueOf(args[2])))
                : text.length();
        return text.lastIndexOf(search, from);
    }
}

package com.fr.function;

import java.util.Calendar;
import java.util.Date;

/**
 * Shared Chinese-numeral conversion used by the FineReport custom functions.
 * Mirrors graft.translate.chinese_convert (the tested Python reference).
 */
public final class ChineseConvertUtil {

    private static final String STD_DIGITS = "零一二三四五六七八九";
    private static final String[] STD_UNITS = {"", "十", "百", "千"};
    private static final String FIN_DIGITS = "零壹貳叄肆伍陸柒捌玖";
    private static final String[] FIN_UNITS = {"", "拾", "佰", "仟"};

    private ChineseConvertUtil() {
    }

    private static Calendar toCalendar(Object value) {
        Calendar c = Calendar.getInstance();
        if (value instanceof Date) {
            c.setTime((Date) value);
            return c;
        }
        String text = String.valueOf(value).trim().replace('/', '-');
        String head = text.split("[ T]")[0];
        String[] parts = head.split("-");
        c.set(Integer.parseInt(parts[0]),
              Integer.parseInt(parts[1]) - 1,
              Integer.parseInt(parts[2]));
        return c;
    }

    public static String dateToChineseYear(Object value) {
        int year = toCalendar(value).get(Calendar.YEAR);
        StringBuilder sb = new StringBuilder();
        for (char ch : String.valueOf(year).toCharArray()) {
            sb.append(STD_DIGITS.charAt(ch - '0'));
        }
        return sb.append("年").toString();
    }

    public static String dateToChineseMonth(Object value) {
        return numberToChinese(toCalendar(value).get(Calendar.MONTH) + 1) + "月";
    }

    public static String dateToChineseDay(Object value) {
        return numberToChinese(toCalendar(value).get(Calendar.DAY_OF_MONTH)) + "日";
    }

    private static String under10000Std(int value) {
        String digits = String.valueOf(value);
        StringBuilder out = new StringBuilder();
        int length = digits.length();
        for (int i = 0; i < length; i++) {
            int d = digits.charAt(i) - '0';
            int pos = length - 1 - i;
            if (d == 0) {
                if (out.length() > 0 && out.charAt(out.length() - 1) != STD_DIGITS.charAt(0)) {
                    out.append(STD_DIGITS.charAt(0));
                }
            } else {
                out.append(STD_DIGITS.charAt(d)).append(STD_UNITS[pos]);
            }
        }
        String text = out.toString();
        while (text.endsWith("零")) {
            text = text.substring(0, text.length() - 1);
        }
        if (text.startsWith("一十")) {
            text = text.substring(1);
        }
        return text;
    }

    public static String numberToChinese(Object value) {
        long n = (long) Math.floor(Double.parseDouble(String.valueOf(value)));
        if (n == 0) {
            return String.valueOf(STD_DIGITS.charAt(0));
        }
        if (n < 0) {
            return "負" + numberToChinese(-n);
        }
        if (n < 10000) {
            return under10000Std((int) n);
        }
        int wan = (int) (n / 10000);
        int rest = (int) (n % 10000);
        String head = under10000Std(wan) + "萬";
        if (rest == 0) {
            return head;
        }
        String bridge = rest < 1000 ? String.valueOf(STD_DIGITS.charAt(0)) : "";
        return head + bridge + under10000Std(rest);
    }

    private static String intToFinancial(long n) {
        if (n == 0) {
            return "";
        }
        String digits = String.valueOf(n);
        StringBuilder out = new StringBuilder();
        int length = digits.length();
        for (int i = 0; i < length; i++) {
            int d = digits.charAt(i) - '0';
            int pos = length - 1 - i;
            int unitInGroup = pos % 4;
            int group = pos / 4;
            if (d == 0) {
                if (out.length() > 0 && out.charAt(out.length() - 1) != FIN_DIGITS.charAt(0)) {
                    out.append(FIN_DIGITS.charAt(0));
                }
            } else {
                out.append(FIN_DIGITS.charAt(d)).append(FIN_UNITS[unitInGroup]);
            }
            if (unitInGroup == 0 && group == 1 && n >= 10000) {
                out.append("萬");
            }
        }
        String text = out.toString();
        while (text.endsWith("零")) {
            text = text.substring(0, text.length() - 1);
        }
        return text;
    }

    public static String decimalToChinese(Object value) {
        long cents = Math.round(Double.parseDouble(String.valueOf(value)) * 100);
        long dollars = cents / 100;
        long remainder = cents % 100;
        long jiao = remainder / 10;
        long fen = remainder % 10;
        StringBuilder sb = new StringBuilder(intToFinancial(dollars)).append("元");
        if (jiao != 0) {
            sb.append(FIN_DIGITS.charAt((int) jiao)).append("角");
        }
        if (fen != 0) {
            sb.append(FIN_DIGITS.charAt((int) fen)).append("分");
        }
        return sb.toString();
    }
}

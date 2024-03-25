def wrap_text(text, fontSize, max_width):
    lines = []
    current_line = ''
    for char in text:
        # 检查将当前字符添加到当前行是否会超过最大宽度
        test_line = current_line + char
        if len(test_line.encode('utf-8')) * fontSize / 2.5 <= max_width:
            # 如果未超过最大宽度，将字符添加到当前行
            current_line = test_line
        else:
            # 如果超过了最大宽度，将当前行添加到行列表中，并开始新的一行
            lines.append(current_line)
            current_line = char
    # 添加最后一行到行列表中
    lines.append(current_line)
    return '\n'.join(lines)

print(wrap_text("美国网友：中国的东西都不安全，食品和华为一样都不安全", 96, 1920))
const supportsColor = process.stdout.isTTY && process.env.TERM !== "dumb";

export const colors = {
  reset: supportsColor ? "\x1b[0m" : "",
  bold: supportsColor ? "\x1b[1m" : "",
  dim: supportsColor ? "\x1b[2m" : "",
  green: supportsColor ? "\x1b[32m" : "",
  red: supportsColor ? "\x1b[31m" : "",
  yellow: supportsColor ? "\x1b[33m" : "",
  blue: supportsColor ? "\x1b[34m" : "",
  cyan: supportsColor ? "\x1b[36m" : "",
  magenta: supportsColor ? "\x1b[35m" : "",
};

export const log = {
  info(msg) {
    console.log(`  ${colors.cyan}i${colors.reset} ${msg}`);
  },
  success(msg) {
    console.log(`  ${colors.green}\u2713${colors.reset} ${msg}`);
  },
  warn(msg) {
    console.log(`  ${colors.yellow}!${colors.reset} ${msg}`);
  },
  error(msg) {
    console.error(`  ${colors.red}\u2717${colors.reset} ${msg}`);
  },
  header(msg) {
    console.log(`\n  ${colors.bold}${msg}${colors.reset}\n`);
  },
};

export function spinner(msg) {
  // Non-TTY: no animation, just log on stop/fail
  if (!process.stdout.isTTY) {
    return {
      stop(finalMsg) {
        console.log(`  \u2713 ${finalMsg}`);
      },
      fail(finalMsg) {
        console.error(`  \u2717 ${finalMsg}`);
      },
    };
  }

  const frames = ["\u280B", "\u2819", "\u2839", "\u2838", "\u283C", "\u2834", "\u2826", "\u2827", "\u2807", "\u280F"];
  let i = 0;
  const id = setInterval(() => {
    process.stdout.write(`\r  ${colors.cyan}${frames[i++ % frames.length]}${colors.reset} ${msg}`);
  }, 80);
  return {
    stop(finalMsg) {
      clearInterval(id);
      process.stdout.write(`\r  ${colors.green}\u2713${colors.reset} ${finalMsg}\n`);
    },
    fail(finalMsg) {
      clearInterval(id);
      process.stdout.write(`\r  ${colors.red}\u2717${colors.reset} ${finalMsg}\n`);
    },
  };
}

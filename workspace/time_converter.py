import datetime
import argparse

def parse_time(input_str, input_format):
    try:
        return datetime.datetime.strptime(input_str, input_format)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid time format: {input_str} (expected: {input_format})")

def format_time(dt, output_format):
    return dt.strftime(output_format)

def main():
    parser = argparse.ArgumentParser(description='Convert time between formats')
    parser.add_argument('input', help='Input time string')
    parser.add_argument('-i', '--input-format', default='%Y-%m-%d %H:%M:%S', help='Input time format (default: ISO8601)')
    parser.add_argument('-o', '--output-format', default='%I:%M %p', help='Output time format (default: 12-hour)')
    args = parser.parse_args()

    try:
        dt = parse_time(args.input, args.input_format)
        result = format_time(dt, args.output_format)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main()

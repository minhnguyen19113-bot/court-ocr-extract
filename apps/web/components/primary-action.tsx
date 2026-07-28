import Link from "next/link";

import { ArrowRight } from "@/components/icons";

interface PrimaryActionBaseProps {
  label: string;
}

interface PrimaryActionLinkProps extends PrimaryActionBaseProps {
  href: string;
  disabled?: false;
}

interface PrimaryActionButtonProps extends PrimaryActionBaseProps {
  disabled: true;
  href?: never;
}

export type PrimaryActionProps =
  | PrimaryActionLinkProps
  | PrimaryActionButtonProps;

export function PrimaryAction(props: Readonly<PrimaryActionProps>) {
  if (props.disabled) {
    return (
      <button className="primary-action" type="button" disabled>
        <span>{props.label}</span>
        <ArrowRight aria-hidden="true" size={18} strokeWidth={1.9} />
      </button>
    );
  }

  return (
    <Link className="primary-action" href={props.href}>
      <span>{props.label}</span>
      <ArrowRight aria-hidden="true" size={18} strokeWidth={1.9} />
    </Link>
  );
}

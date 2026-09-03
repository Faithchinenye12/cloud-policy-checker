type BrandMarkProps = { className?: string };

export default function BrandMark({ className = "" }: BrandMarkProps) {
  return <img className={`brand-mark ${className}`.trim()} src="/cfb-mark.png" alt="" aria-hidden="true" />;
}

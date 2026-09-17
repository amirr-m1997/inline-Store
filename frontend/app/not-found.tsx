import Link from "next/link";

export default function NotFound() {
  return (
    <main className="container-page py-16 text-center">
      <h1>404</h1>
      <p>
        <Link href="/fa">بازگشت به فروشگاه</Link> · <Link href="/en">Back to store</Link>
      </p>
    </main>
  );
}
